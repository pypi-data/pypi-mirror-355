//! Nom floating point numbers parser
//!
//! This is direct port of the nom recipe here: https://docs.rs/nom/latest/nom/recipes/index.html#floating-point-numbers
use nom::{
    IResult,
    branch::alt,
    character::complete::{char, one_of},
    combinator::{opt, recognize},
    error::{FromExternalError, ParseError},
    multi::{many0, many1},
    sequence::{preceded, terminated, tuple},
};

pub(super) fn float1<'a, E>(input: &'a str) -> IResult<&'a str, &'a str, E>
where
    E: ParseError<&'a str> + FromExternalError<&'a str, std::num::ParseIntError>,
{
    tracing::trace!("Recognize float in {}", input);
    let res = alt((
        // Case one: .42
        recognize(tuple((
            char('.'),
            decimal,
            opt(tuple((one_of("eE"), opt(one_of("+-")), decimal))),
        ))), // Case two: 42e42 and 42.42e42
        recognize(tuple((
            decimal,
            opt(preceded(char('.'), decimal)),
            one_of("eE"),
            opt(one_of("+-")),
            decimal,
        ))), // Case three: 42. and 42.42
        recognize(tuple((decimal, char('.'), opt(decimal)))),
    ))(input);
    if let Ok(ref res) = res {
        tracing::trace!("Float res {:?} => {:?}", res.0, res.1);
    }
    res
}

fn decimal<'a, E>(input: &'a str) -> IResult<&'a str, &'a str, E>
where
    E: ParseError<&'a str> + FromExternalError<&'a str, std::num::ParseIntError>,
{
    recognize(many1(terminated(one_of("0123456789"), many0(char('_')))))(input)
}
