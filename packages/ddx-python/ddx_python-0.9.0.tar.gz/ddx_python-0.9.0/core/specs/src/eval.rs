/// In this example we build an [S-expression](https://en.wikipedia.org/wiki/S-expression)
/// parser and tiny [lisp](https://en.wikipedia.org/wiki/Lisp_(programming_language)) interpreter.
///
/// Lisp is a simple type of language made up of Atoms and Lists, forming easily parsable trees.
use super::{float_parser::float1, str_parser::parse_string};
use core_common::{Error, Result, bail, ensure, error, types::primitives::UnscaledI128};
use dyn_fmt::Arguments;
use nom::{
    AsChar, IResult, Parser,
    branch::alt,
    bytes::complete::{tag, take_while1},
    character::complete::{char, digit1, multispace0, multispace1, one_of},
    combinator::{cut, map, map_res, opt},
    error::{VerboseError, context},
    multi::{many0, many1, separated_list1},
    sequence::{delimited, preceded, terminated, tuple},
};
#[cfg(feature = "arbitrary")]
use quickcheck::Arbitrary;
use regex::Regex;
use rust_decimal::{
    Decimal,
    prelude::{One, ToPrimitive, Zero},
};
use serde::{Deserialize, Serialize};
use std::{convert::TryFrom, ops::Neg};

/// We start by defining the types that define the shape of data that we want.
/// In this case, we want something tree-like
///
/// Starting from the most basic, we define some built-in functions that our lisp has
#[derive(Debug, PartialEq, Clone)]
pub enum BuiltIn {
    Plus,
    Minus,
    Times,
    Divide,
    Equal,
    Not,
    // Transform utils
    Transform,
    Sed,
    Jq,
    Format,
    Chained,
    // Data structures
    Make(String),
    // Debug utils
    Write,
}

#[derive(Debug, PartialEq, Clone, Deserialize, Serialize)]
pub enum Transform {
    Sed(String),
    Jq(String),
    Format(String),
    Chained(Vec<Transform>),
    Passthrough,
}

impl Transform {
    /// Applies the transform pattern to the input.
    ///
    /// This return a copy of the input string after applying the pattern. This does not support multiple
    /// inputs. For example, the `Format` op is limited to just one argument `format!("My Transform Pattern: {}", input)`.
    pub fn apply(&self, mut input: String) -> Result<String> {
        let out = match self {
            Transform::Chained(transforms) => {
                for transform in transforms {
                    input = transform.apply(input)?;
                }
                input
            }
            Transform::Format(template) => {
                format!("{}", Arguments::new(template, &[input]))
            }
            Transform::Jq(query) => {
                ensure!(gjson::valid(&input), "Expected JSON input, got {}", input);
                let value = gjson::get(&input, query);
                value.to_string()
            }
            Transform::Sed(pattern) => {
                let patterns = pattern
                    .split(';')
                    .filter_map(|p| {
                        if p.trim().is_empty() {
                            None
                        } else {
                            Some(p.trim())
                        }
                    })
                    .filter_map(|sed| {
                        // Shortest possible expression `s/x//` == 5
                        if !sed.starts_with('s') || sed.len() < 5 {
                            return None;
                        }
                        let delim = &sed[1..2];
                        // Splitting the pattern after the `s/` (or whatever delimiter).
                        let parts = sed[2..].split(delim).collect::<Vec<_>>();
                        tracing::debug!(
                            "Found sed pattern {} - Delim {} - Parts {:?}",
                            sed,
                            delim,
                            parts
                        );
                        // Return both the source and destination, or nothing at all.
                        parts.first().and_then(|s| parts.get(1).map(|d| (*s, *d)))
                    })
                    .collect::<Vec<_>>();
                // Chain the replacers
                for (pat, rep) in patterns {
                    tracing::debug!("With input '{}', replace {} by {}", input, pat, rep);
                    let re = Regex::new(pat)?;
                    input = re.replace(&input, rep).to_string();
                    tracing::debug!("Result {}", input);
                }
                input
            }
            Transform::Passthrough => input,
        };
        Ok(out)
    }
}

#[cfg(feature = "arbitrary")]
impl Arbitrary for Transform {
    fn arbitrary(g: &mut quickcheck::Gen) -> Self {
        // TODO: Add the other variants
        let discriminator = *g.choose(&[0]).unwrap();
        match discriminator {
            0 => Self::Passthrough,
            _ => panic!("Invalid discriminator"),
        }
    }
}

#[derive(Debug, PartialEq, Clone)]
pub struct StructRepr {
    pub name: String,
    fields: Vec<(String, Atom)>,
}

impl StructRepr {
    pub fn ensure_match(&self, name: &str, min_fields: usize) -> Result<()> {
        ensure!(
            self.name.to_lowercase() == name.to_lowercase(),
            "Expected {}, got {}",
            name,
            self.name
        );
        ensure!(
            min_fields <= self.fields.len(),
            "Expected {} fields, got {}",
            min_fields,
            self.fields.len()
        );
        Ok(())
    }

    /// Take field value unchecked.
    ///
    /// Do not use with external inputs.
    #[cfg(test)]
    pub fn take(&mut self, key: &str) -> Atom {
        self.try_take(key).unwrap()
    }

    pub fn try_take(&mut self, key: &str) -> Result<Atom> {
        let mut items = self
            .fields
            .extract_if(|(k, _v)| k.as_str() == key)
            .map(|f| f.1)
            .collect::<Vec<_>>();
        ensure!(
            items.len() == 1,
            "Expected field {} to have exactly one value",
            key
        );
        Ok(items.remove(0))
    }

    pub fn take_items(&mut self, prefix: &str) -> Vec<(String, Atom)> {
        self.fields
            .extract_if(|(k, _v)| k.starts_with(prefix))
            .collect()
    }
}

/// We now wrap this type and a few other primitives into our Atom type.
/// Remember from before that Atoms form one half of our language.
#[derive(Debug, PartialEq, Clone)]
pub enum Atom {
    Num(Decimal),
    Keyword(String),
    Boolean(bool),
    BuiltIn(BuiltIn),
    Str(String),
    Void,
    Transform(Transform),
    Struct(StructRepr),
    List(Vec<Atom>),
}

impl Atom {
    #[cfg(test)]
    pub fn into_num(self) -> Decimal {
        self.try_into().unwrap()
    }

    #[cfg(test)]
    pub fn into_string(self) -> String {
        self.try_into().unwrap()
    }

    pub fn try_struct(self) -> Result<StructRepr> {
        if let Atom::Struct(v) = self {
            Ok(v)
        } else {
            Err(error!("Wrong type {:?}", self))
        }
    }

    pub fn try_list(self) -> Result<Vec<Atom>> {
        if let Atom::List(v) = self {
            Ok(v)
        } else {
            Err(error!("Wrong type {:?}", self))
        }
    }
}

impl TryFrom<Atom> for String {
    type Error = Error;

    fn try_from(value: Atom) -> Result<Self, Self::Error> {
        if let Atom::Str(v) = value {
            Ok(v)
        } else {
            Err(error!("Wrong type {:?}", value))
        }
    }
}

impl TryFrom<Atom> for Transform {
    type Error = Error;

    fn try_from(value: Atom) -> Result<Self, Self::Error> {
        if let Atom::Transform(v) = value {
            Ok(v)
        } else {
            Err(error!("Wrong type {:?}", value))
        }
    }
}

impl TryFrom<Atom> for u64 {
    type Error = Error;

    fn try_from(value: Atom) -> Result<Self, Self::Error> {
        if let Atom::Num(v) = value {
            Ok(v.to_u64().ok_or_else(|| error!("Invalid u64"))?)
        } else {
            Err(error!("Wrong type {:?}", value))
        }
    }
}

impl TryFrom<Atom> for Decimal {
    type Error = Error;

    fn try_from(value: Atom) -> Result<Self, Self::Error> {
        if let Atom::Num(v) = value {
            Ok(v)
        } else {
            Err(error!("Wrong type {:?}", value))
        }
    }
}

impl TryFrom<Atom> for UnscaledI128 {
    type Error = Error;

    fn try_from(value: Atom) -> Result<Self, Self::Error> {
        if let Atom::Num(v) = value {
            Ok(UnscaledI128::new(v))
        } else {
            Err(error!("Wrong type {:?}", value))
        }
    }
}

#[derive(Debug, PartialEq, Clone)]
pub enum Expr {
    Constant(Atom),
    /// (func-name arg1 arg2)
    Application(Box<Expr>, Vec<Expr>),
    /// (if predicate do-this)
    If(Box<Expr>, Box<Expr>),
    /// (if predicate do-this otherwise-do-this)
    IfElse(Box<Expr>, Box<Expr>, Box<Expr>),
    /// '(3 (if (+ 3 3) 4 5) 7)
    Quote(Vec<Expr>),
}

/// Continuing the trend of starting from the simplest piece and building up,
/// we start by creating a parser for the built-in operator functions.
fn parse_builtin_op(i: &str) -> IResult<&str, BuiltIn, VerboseError<&str>> {
    // one_of matches one of the characters we give it
    let (i, t) = one_of("+-*/=")(i)?;

    // because we are matching single character tokens, we can do the matching logic
    // on the returned value
    Ok((
        i,
        match t {
            '+' => BuiltIn::Plus,
            '-' => BuiltIn::Minus,
            '*' => BuiltIn::Times,
            '/' => BuiltIn::Divide,
            '=' => BuiltIn::Equal,
            _ => unreachable!(),
        },
    ))
}

fn parse_builtin(i: &str) -> IResult<&str, BuiltIn, VerboseError<&str>> {
    // alt gives us the result of first parser that succeeds, of the series of
    // parsers we give it
    alt((
        parse_builtin_op,
        // map lets us process the parsed output, in this case we know what we parsed,
        // so we ignore the input and return the BuiltIn directly
        map(tag("not"), |_| BuiltIn::Not),
        map(tag("sed"), |_| BuiltIn::Sed),
        map(tag("jq"), |_| BuiltIn::Jq),
        map(tag("format"), |_| BuiltIn::Format),
        map(tag("chain"), |_| BuiltIn::Chained),
        map(tag("write"), |_| BuiltIn::Write),
        map(tag("transform"), |_| BuiltIn::Transform),
        map(parse_make, BuiltIn::Make),
        // map(
        //     preceded(tag("make-"), kebab_case),
        //     // separated_pair(tag("make"), char('-'), alt((alpha1, is_a("-")))),
        //     |expr| {
        //         tracing::debug!("Make cmd {:?}", expr);
        //         BuiltIn::Make(expr)
        //     },
        // ),
    ))(i)
}

fn parse_str(i: &str) -> IResult<&str, Atom, VerboseError<&str>> {
    parse_string(i).map(|(n, v)| (n, Atom::Str(v)))
}

/// Our boolean values are also constant, so we can do it the same way
fn parse_bool(i: &str) -> IResult<&str, Atom, VerboseError<&str>> {
    alt((
        map(tag("#t"), |_| Atom::Boolean(true)),
        map(tag("#f"), |_| Atom::Boolean(false)),
    ))(i)
}

fn camel_case_word(i: &str) -> IResult<&str, String, VerboseError<&str>> {
    let (tail, u) = take_while1(|c: char| c.is_alpha() && c.is_uppercase())(i)?;
    // tracing::debug!("Camel case letter {} - Tail {}", u, tail);
    // NOTE - Purposefully restrictive, single capital letter does not count as camel case.
    let (tail, l) = take_while1(|c: char| c.is_alpha() && c.is_lowercase())(tail)?;
    Ok((tail, format!("{}{}", u, l)))
}

fn camel_case(i: &str) -> IResult<&str, String, VerboseError<&str>> {
    map(many1(camel_case_word), |words| words.join(""))(i)
}

fn parse_make(i: &str) -> IResult<&str, String, VerboseError<&str>> {
    // NOTE: Counting on the parser control flow not to detect false positives.
    context("make", camel_case)(i)
}

fn kebab_case(i: &str) -> IResult<&str, String, VerboseError<&str>> {
    map(
        separated_list1(
            tag("-"),
            take_while1(|c: char| c.is_alphanum() && c.is_lowercase()),
        ),
        |l: Vec<&str>| l.join("-"),
    )(i)
}

/// he next easiest thing to parse are keywords.
/// We introduce some error handling combinators: `context` for human readable errors
/// and `cut` to prevent back-tracking.
///
/// Put plainly: `preceded(tag(":"), cut(alpha1))` means that once we see the `:`
/// character, we have to see one or more alphabetic characters or the input is invalid.
fn parse_keyword(i: &str) -> IResult<&str, Atom, VerboseError<&str>> {
    map(
        context("keyword", preceded(tag(":"), cut(kebab_case))),
        Atom::Keyword,
    )(i)
}

/// Next up is number parsing. We're keeping it simple here by accepting any number (> 1)
/// of digits but ending the program if it doesn't fit into an Decimal.
///
/// This first recognizes a float pattern and then falls back to a digit pattern.
fn parse_num(i: &str) -> IResult<&str, Atom, VerboseError<&str>> {
    let res = alt((
        map_res(alt((float1, digit1)), |float_str: &str| {
            tracing::debug!("Parsing float {}", float_str);
            let d = float_str.parse::<Decimal>().map(Atom::Num);
            tracing::debug!("The decimal {:?}", d);
            d
        }),
        map_res(
            preceded(tag("-"), alt((float1, digit1))),
            |float_str: &str| {
                tracing::debug!("Parsing negative float {}", float_str);
                float_str
                    .parse::<Decimal>()
                    .map(|f| f * Decimal::one().neg())
                    .map(Atom::Num)
            },
        ),
    ))(i);
    if let Ok(ref res) = res {
        tracing::debug!("Parse num res {:?} => {:?}", res.0, res.1);
    }
    res
}

/// Now we take all these simple parsers and connect them.
/// We can now parse half of our language!
fn parse_atom(i: &str) -> IResult<&str, Atom, VerboseError<&str>> {
    alt((
        parse_num,
        parse_bool,
        map(parse_builtin, Atom::BuiltIn),
        parse_keyword,
        parse_str,
    ))(i)
}

/// We then add the Expr layer on top
fn parse_constant(i: &str) -> IResult<&str, Expr, VerboseError<&str>> {
    map(parse_atom, Expr::Constant)(i)
}

/// Before continuing, we need a helper function to parse lists.
/// A list starts with `(` and ends with a matching `)`.
/// By putting whitespace and newline parsing here, we can avoid having to worry about it
/// in much of the rest of the parser.
///
/// Unlike the previous functions, this function doesn't take or consume input, instead it
/// takes a parsing function and returns a new parsing function.
fn s_exp<'a, O1, F>(inner: F) -> impl FnMut(&'a str) -> IResult<&'a str, O1, VerboseError<&'a str>>
where
    F: Parser<&'a str, O1, VerboseError<&'a str>>,
{
    delimited(
        char('('),
        preceded(multispace0, inner),
        context("closing paren", cut(preceded(multispace0, char(')')))),
    )
}

/// We can now use our new combinator to define the rest of the `Expr`s.
///
/// Starting with function application, we can see how the parser mirrors our data
/// definitions: our definition is `Application(Box<Expr>, Vec<Expr>)`, so we know
/// that we need to parse an expression and then parse 0 or more expressions, all
/// wrapped in an S-expression.
///
/// `tuple` is used to sequence parsers together, so we can translate this directly
/// and then map over it to transform the output into an `Expr::Application`
fn parse_application(i: &str) -> IResult<&str, Expr, VerboseError<&str>> {
    let application_inner = map(tuple((parse_expr, many0(parse_expr))), |(head, tail)| {
        Expr::Application(Box::new(head), tail)
    });
    // finally, we wrap it in an s-expression
    s_exp(application_inner)(i)
}

/// Because `Expr::If` and `Expr::IfElse` are so similar (we easily could have
/// defined `Expr::If` to have an `Option` for the else block), we parse both
/// in a single function.
///
/// In fact, we define our parser as if `Expr::If` was defined with an Option in it,
/// we have the `opt` combinator which fits very nicely here.
fn parse_if(i: &str) -> IResult<&str, Expr, VerboseError<&str>> {
    let if_inner = context(
        "if expression",
        map(
            preceded(
                // here to avoid ambiguity with other names starting with `if`, if we added
                // variables to our language, we say that if must be terminated by at least
                // one whitespace character
                terminated(tag("if"), multispace1),
                cut(tuple((parse_expr, parse_expr, opt(parse_expr)))),
            ),
            |(pred, true_branch, maybe_false_branch)| {
                if let Some(false_branch) = maybe_false_branch {
                    Expr::IfElse(
                        Box::new(pred),
                        Box::new(true_branch),
                        Box::new(false_branch),
                    )
                } else {
                    Expr::If(Box::new(pred), Box::new(true_branch))
                }
            },
        ),
    );
    s_exp(if_inner)(i)
}

/// A quoted S-expression is list data structure.
///
/// This example doesn't have the symbol atom, but by adding variables and changing
/// the definition of quote to not always be around an S-expression, we'd get them
/// naturally.
fn parse_quote(i: &str) -> IResult<&str, Expr, VerboseError<&str>> {
    // this should look very straight-forward after all we've done:
    // we find the `'` (quote) character, use cut to say that we're unambiguously
    // looking for an s-expression of 0 or more expressions, and then parse them
    map(
        context("quote", preceded(tag("'"), cut(s_exp(many0(parse_expr))))),
        Expr::Quote,
    )(i)
}

/// We tie them all together again, making a top-level expression parser!
fn parse_expr(i: &str) -> IResult<&str, Expr, VerboseError<&str>> {
    preceded(
        multispace0,
        alt((parse_constant, parse_application, parse_if, parse_quote)),
    )(i)
}

/// And that's it!
/// We can now parse our entire lisp language.
///
/// But in order to make it a little more interesting, we can hack together
/// a little interpreter to take an Expr, which is really an
/// [Abstract Syntax Tree](https://en.wikipedia.org/wiki/Abstract_syntax_tree) (AST),
/// and give us something back
///
/// To start we define a couple of helper functions
fn get_num_from_expr(e: Expr) -> Option<Decimal> {
    if let Expr::Constant(Atom::Num(n)) = e {
        Some(n)
    } else {
        None
    }
}

fn get_bool_from_expr(e: Expr) -> Option<bool> {
    if let Expr::Constant(Atom::Boolean(b)) = e {
        Some(b)
    } else {
        None
    }
}

fn ensure_cast<T>(res: Option<T>) -> Result<T> {
    res.ok_or_else(|| error!("Unable to cast the expr into the given type"))
}

/// Tries to reduce the AST.
///
/// This has to return an Expression rather than an Atom because quoted s_expressions
/// can't be reduced
// NOTE: Allowing unreachable code until blackbox testing covers all keywords.
#[allow(unused_variables)]
#[allow(unreachable_code)]
fn eval_expression(e: Expr) -> Result<Expr> {
    match e {
        // Constants and quoted s-expressions are our base-case
        Expr::Constant(_) | Expr::Quote(_) => Ok(e),
        // we then recursively `eval_expression` in the context of our special forms
        // and built-in operators
        Expr::If(pred, true_branch) => {
            bail!("If op not yet supported");
            let reduce_pred = eval_expression(*pred)?;
            if ensure_cast(get_bool_from_expr(reduce_pred))? {
                eval_expression(*true_branch)
            } else {
                bail!("Invalid if expr");
            }
        }
        Expr::IfElse(pred, true_branch, false_branch) => {
            bail!("IfElse op not yet supported");
            let reduce_pred = eval_expression(*pred)?;
            if ensure_cast(get_bool_from_expr(reduce_pred))? {
                eval_expression(*true_branch)
            } else {
                eval_expression(*false_branch)
            }
        }
        Expr::Application(head, tail) => {
            let reduced_head = eval_expression(*head)?;
            let reduced_tail = tail
                .into_iter()
                .map(eval_expression)
                .collect::<Result<Vec<Expr>, _>>()?;
            if let Expr::Constant(Atom::BuiltIn(bi)) = reduced_head {
                let res = Expr::Constant(match bi {
                    BuiltIn::Chained => {
                        let mut transforms = Vec::with_capacity(reduced_tail.len());
                        for expr in reduced_tail.iter().cloned() {
                            if let Expr::Constant(Atom::Transform(transform)) = expr {
                                transforms.push(transform);
                            } else {
                                bail!("Not a transform");
                            }
                        }
                        Atom::Transform(Transform::Chained(transforms))
                    }
                    BuiltIn::Sed => {
                        if reduced_tail.len() != 1 {
                            bail!("Invalid sed expr");
                        }
                        let expr = reduced_tail.first().cloned().unwrap();
                        if let Expr::Constant(Atom::Str(content)) = expr {
                            Atom::Transform(Transform::Sed(content))
                        } else {
                            bail!("Not a string");
                        }
                    }
                    BuiltIn::Jq => {
                        if reduced_tail.len() != 1 {
                            bail!("Invalid jq expr");
                        }
                        let expr = reduced_tail.first().cloned().unwrap();
                        if let Expr::Constant(Atom::Str(content)) = expr {
                            Atom::Transform(Transform::Jq(content))
                        } else {
                            bail!("Not a string");
                        }
                    }
                    BuiltIn::Format => {
                        if reduced_tail.len() != 1 {
                            bail!("Invalid format expr");
                        }
                        let expr = reduced_tail.first().cloned().unwrap();
                        if let Expr::Constant(Atom::Str(content)) = expr {
                            Atom::Transform(Transform::Format(content))
                        } else {
                            bail!("Not a string");
                        }
                    }
                    BuiltIn::Make(name) => {
                        // Must at least name the struct, followed by fields if any.
                        if reduced_tail.is_empty() {
                            bail!("Invalid make expr");
                        }
                        let mut fields = Vec::with_capacity(reduced_tail.len() / 2);
                        // Assuming that expressions are always stored in order.
                        for chunk in reduced_tail.chunks_exact(2) {
                            if let Expr::Constant(Atom::Keyword(ref field)) = chunk[0] {
                                match chunk[1] {
                                    Expr::Constant(ref atom) => {
                                        fields.push((field.clone(), atom.clone()));
                                    }
                                    Expr::Quote(ref constants) => {
                                        let atoms = constants
                                            .iter()
                                            .map(|e| {
                                                if let Expr::Constant(a) = e {
                                                    Ok(a.clone())
                                                } else {
                                                    Err(error!("Lists can only contain atoms"))
                                                }
                                            })
                                            .collect::<Result<Vec<_>>>()?;
                                        fields.push((field.clone(), Atom::List(atoms)));
                                    }
                                    // This should already be reduced so nothing else to evaluate.
                                    _ => bail!("Unexpected field {:?}", chunk),
                                }
                            }
                        }
                        Atom::Struct(StructRepr { name, fields })
                    }
                    BuiltIn::Transform => {
                        if reduced_tail.len() != 2 {
                            bail!("Invalid transform expr");
                        }
                        let left = reduced_tail.first().cloned().unwrap();
                        let right = reduced_tail.last().cloned().unwrap();
                        match (left, right) {
                            (
                                Expr::Constant(Atom::Transform(transform)),
                                Expr::Constant(Atom::Str(input)),
                            ) => {
                                // tracing::debug!("transform> {} \n  => {:?}", input, transform);
                                Atom::Str(transform.apply(input)?)
                            }
                            _ => {
                                bail!("Expected a transform folled by input");
                            }
                        }
                    }
                    BuiltIn::Write => {
                        if reduced_tail.len() != 1 {
                            bail!("Invalid write expr");
                        }
                        let expr = reduced_tail.first().cloned().unwrap();
                        match expr {
                            Expr::Constant(Atom::Num(content)) => {
                                tracing::debug!("num> {}", content);
                            }
                            Expr::Constant(Atom::Str(content)) => {
                                tracing::debug!("str> {}", content);
                            }
                            _ => {
                                tracing::debug!("debug> {:?}", expr);
                            }
                        }
                        Atom::Void
                    }
                    BuiltIn::Plus => {
                        bail!("Plus op not yet supported");
                        Atom::Num(
                            ensure_cast(
                                reduced_tail
                                    .into_iter()
                                    .map(get_num_from_expr)
                                    .collect::<Option<Vec<Decimal>>>(),
                            )?
                            .into_iter()
                            .sum(),
                        )
                    }
                    BuiltIn::Times => {
                        bail!("Times op not yet supported");
                        Atom::Num(
                            ensure_cast(
                                reduced_tail
                                    .into_iter()
                                    .map(get_num_from_expr)
                                    .collect::<Option<Vec<Decimal>>>(),
                            )?
                            .into_iter()
                            .fold(Decimal::zero(), |acc, x| acc * x),
                        )
                    }
                    BuiltIn::Equal => {
                        bail!("Equal op not yet supported");
                        Atom::Boolean(
                            reduced_tail
                                .iter()
                                .zip(reduced_tail.iter().skip(1))
                                .all(|(a, b)| a == b),
                        )
                    }
                    BuiltIn::Not => {
                        bail!("Not op not yet supported");
                        if reduced_tail.len() != 1 {
                            bail!("Invalid not expr");
                        } else {
                            Atom::Boolean(!ensure_cast(get_bool_from_expr(
                                reduced_tail.first().cloned().unwrap(),
                            ))?)
                        }
                    }
                    BuiltIn::Minus => {
                        bail!("Minus op not yet supported");
                        Atom::Num(if let Some(first_elem) = reduced_tail.first().cloned() {
                            let fe = ensure_cast(get_num_from_expr(first_elem))?;
                            ensure_cast(
                                reduced_tail
                                    .into_iter()
                                    .map(get_num_from_expr)
                                    .collect::<Option<Vec<Decimal>>>(),
                            )?
                            .into_iter()
                            .skip(1)
                            .fold(fe, |a, b| a - b)
                        } else {
                            Default::default()
                        })
                    }
                    BuiltIn::Divide => {
                        bail!("Minus op not yet supported");
                        Atom::Num(if let Some(first_elem) = reduced_tail.first().cloned() {
                            let fe = ensure_cast(get_num_from_expr(first_elem))?;
                            ensure_cast(
                                reduced_tail
                                    .into_iter()
                                    .map(get_num_from_expr)
                                    .collect::<Option<Vec<Decimal>>>(),
                            )?
                            .into_iter()
                            .skip(1)
                            .fold(fe, |a, b| a / b)
                        } else {
                            Default::default()
                        })
                    }
                });
                Ok(res)
            } else {
                Err(Error::Parse("Unexpected parse error".to_string()))
            }
        }
    }
}

/// And we add one more top-level function to tie everything together, letting
/// us call eval on a string directly
pub fn eval_from_str(src: &str) -> Result<Expr> {
    parse_expr(src)
        .map_err(|e: nom::Err<VerboseError<&str>>| Error::Parse(format!("Parsing error {:?}", e)))
        .and_then(|(_, exp)| eval_expression(exp))
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_chain() {
        let write1 = r#"(chain (jq "[price]") (sed "s/\\[([0-9\\.]+)\\]/[\"DDX\",$1]/;"))"#;
        assert!(eval_from_str(write1).is_ok());
    }

    #[test]
    fn test_builtin() {
        let expression_1 = "((if (= (+ 3 (/ 9 3))
         (* 2 3))
     *
     /)
  456 123)";
        // TODO: Conditional expressions and arithmetics not supported until blackbox tested.
        assert!(eval_from_str(expression_1).is_err());

        let quote1 = r#"(write '(3 (if (+ 3 3) 4 5) 7))"#;
        let _expr = eval_from_str(quote1).unwrap();

        let quote2 = r#"(write '(format "/api/v3/ticker/price?symbol=%s"))"#;
        let expr = eval_from_str(quote2).unwrap();
        tracing::debug!("\"{}\" \n  => {:?}", quote2, expr);
    }

    #[test]
    fn test_write() {
        let write1 = r#"(write (+ 1 1))"#;
        assert!(eval_from_str(write1).is_err());

        let write2 = r#"(write "hello world")"#;
        tracing::debug!("\"{}\" \n  => {:?}", write2, eval_from_str(write2).unwrap());
    }

    #[test]
    fn test_format() {
        // See syntax: https://github.com/A1-Triard/dyn-fmt
        let format1 = r#"(format "/api/v3/ticker/price?symbol={}")"#;
        let expr = eval_from_str(format1).unwrap();
        tracing::debug!("\"{}\" \n  => {:?}", format1, expr,);

        let format2 = r#"(transform (format "/api/v3/ticker/price?symbol={}") "ETHUSDC")"#;
        let expr = eval_from_str(format2).unwrap();
        tracing::debug!("\"{}\" \n  => {:?}", format2, expr,);
    }

    #[test]
    fn test_jq() {
        // See syntax: https://github.com/tidwall/gjson/blob/master/SYNTAX.md#modifiers
        let jq1 = r#"(jq "[symbol,price]")"#;
        let expr = eval_from_str(jq1).unwrap();
        tracing::debug!("\"{}\" \n  => {:?}", jq1, expr);
        let jq2 = r#"(transform (jq "[symbol,price]") "{\"price\": \"204.70000000\", \"symbol\": \"XMRUSDT\"}")"#;
        let expr = eval_from_str(jq2).unwrap();
        tracing::debug!("\"{}\" \n  => {:?}", jq2, expr);
    }

    #[test]
    fn test_sed() {
        // See syntax: https://docs.rs/regex/1.3.1/regex/struct.Regex.html#method.replace
        let sed1 = r#"(sed "s/foo/bar/;")"#;
        assert_eq!(
            Expr::Constant(Atom::Transform(Transform::Sed("s/foo/bar/;".to_string()))),
            eval_from_str(sed1).unwrap()
        );
        let sed2 = r#"(transform (sed "s/foo/bar/;") "I'm going to the foo")"#;
        assert_eq!(
            Expr::Constant(Atom::Str("I'm going to the bar".to_string())),
            eval_from_str(sed2).unwrap()
        );
        let sed3 = r#"(transform (sed "s/(?P<last>[^,\\s]+),\\s+(?P<first>\\S+)/$first $last/;") "Springsteen, Bruce")"#;
        assert_eq!(
            Expr::Constant(Atom::Str("Bruce Springsteen".to_string())),
            eval_from_str(sed3).unwrap(),
        );
        let sed4 = r#"(transform (sed "s/(?P<base>[A-Z]+)/${base}USDC/;") "ETH")"#;
        assert_eq!(
            Expr::Constant(Atom::Str("ETHUSDC".to_string())),
            eval_from_str(sed4).unwrap(),
        );
        let sed5 = r#"(sed "s/\\[([0-9\\.]+)\\]/[\"DDX\",$1]/;"))"#;
        assert_eq!(
            Expr::Constant(Atom::Transform(Transform::Sed(
                r#"s/\[([0-9\.]+)\]/["DDX",$1]/;"#.to_string()
            ))),
            eval_from_str(sed5).unwrap()
        )
    }

    #[test]
    fn test_struct() {
        #[derive(Debug, PartialEq, Clone)]
        struct Test {
            foo: Decimal,
            bar: String,
        }

        impl From<StructRepr> for Test {
            fn from(mut repr: StructRepr) -> Self {
                repr.ensure_match("test", 2).unwrap();
                Test {
                    foo: repr.take("foo").into_num(),
                    bar: repr.take("bar").into_string(),
                }
            }
        }

        let want = Test {
            foo: Decimal::one(),
            bar: "hello".to_string(),
        };

        let struct1 = r#"(Test :foo 1 :bar "hello")"#;
        let res = eval_from_str(struct1).unwrap();
        tracing::debug!("\"{}\" \n  => {:?}", struct1, res);
        if let Expr::Constant(Atom::Struct(repr)) = res {
            assert_eq!(want, repr.into());
        } else {
            panic!("Unexpected parser expression");
        }
    }

    #[test]
    fn test_casing() {
        let k = "kebab-case 12345";
        let out = kebab_case(k).unwrap();
        assert_eq!(out, (" 12345", "kebab-case".to_string()));

        let k = "12345 kebab-case";
        assert!(kebab_case(k).is_err());

        let k = "kebab 12345";
        let out = kebab_case(k).unwrap();
        assert_eq!(out, (" 12345", "kebab".to_string()));

        let c = "CamelCase 12345";
        let out = camel_case(c).unwrap();
        assert_eq!(out, (" 12345", "CamelCase".to_string()));

        let c = "Camel 12345";
        let out = camel_case(c).unwrap();
        assert_eq!(out, (" 12345", "Camel".to_string()));

        let c = "C 12345";
        assert!(camel_case(c).is_err());

        let c = "camelcase 12345";
        assert!(camel_case(c).is_err());

        let c = "Camel-Case 12345";
        let out = camel_case(c).unwrap();
        assert_eq!(out, ("-Case 12345", "Camel".to_string()));

        let c = "kebab-Case 12345";
        let out = kebab_case(c).unwrap();
        assert_eq!(out, ("-Case 12345", "kebab".to_string()));

        let c = "Kebab-Case 12345";
        assert!(kebab_case(c).is_err());
    }
}
