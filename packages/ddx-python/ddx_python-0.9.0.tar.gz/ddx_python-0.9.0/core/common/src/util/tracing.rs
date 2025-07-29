use tracing_subscriber::{
    EnvFilter, Layer,
    fmt::{format::FmtSpan, time::UtcTime},
    layer::SubscriberExt,
    util::SubscriberInitExt,
};
/// Format of tracing event written to stdout.
///
/// Using JSON is the default, and usually necessary to collect system metrics.
/// However, using pretty logs is more human readable and useful for development.
/// As a general rule, use JSON in a network configuration and pretty for local development.
#[derive(Debug, Clone, Copy)]
pub enum StdoutFormat {
    Json,
    Pretty,
}

/// Initializes the global tracing subscriber using the given format.
///
/// The stdout log filter is configured via the `RUST_LOG` environment variable.
///
/// If enabled via the "console" feature, the console subscriber is configured as follows:
///
/// | **Environment Variable**         | **Purpose**                                                  | **Default Value** |
/// |----------------------------------|--------------------------------------------------------------|-------------------|
/// | `TOKIO_CONSOLE_RETENTION`        | The duration of seconds to accumulate completed tracing data | 3600s (1h)        |
/// | `TOKIO_CONSOLE_BIND`             | a HOST:PORT description, such as `localhost:1234`            | `127.0.0.1:6669`  |
/// | `TOKIO_CONSOLE_PUBLISH_INTERVAL` | The duration to wait between sending updates to the console  | 1000ms (1s)       |
/// | `TOKIO_CONSOLE_RECORD_PATH`      | The file path to save a recording                            | None              |
pub fn init_tracing(presentation: StdoutFormat) {
    match presentation {
        StdoutFormat::Json => {
            // TODO: Consider a separate layer to push to the metrics schema instead of using stdout for better better separation of concerns.
            let fmt = tracing_subscriber::fmt::layer()
                .json()
                .with_span_events(FmtSpan::CLOSE)
                .with_thread_ids(true)
                .with_timer(UtcTime::rfc_3339())
                .with_current_span(true)
                .with_span_list(false)
                .flatten_event(true);
            // Repeating this block in each branch because both `Layer` and `Layered` have many generics, so their types don't match.
            #[cfg(feature = "console")]
            {
                let filter = EnvFilter::from_default_env()
                    .add_directive("tokio=trace".parse().unwrap())
                    .add_directive("runtime=trace".parse().unwrap());
                let subscriber = tracing_subscriber::registry().with(fmt.with_filter(filter));
                let _ = subscriber.with(console_subscriber::spawn()).try_init();
            }
            #[cfg(not(feature = "console"))]
            {
                let _ = tracing_subscriber::registry()
                    .with(fmt.with_filter(EnvFilter::from_default_env()))
                    .try_init();
            }
        }
        StdoutFormat::Pretty => {
            let fmt = tracing_subscriber::fmt::layer()
                .pretty()
                .with_ansi(true)
                .with_span_events(FmtSpan::ENTER | FmtSpan::CLOSE)
                .with_thread_ids(true)
                .with_timer(UtcTime::new(
                    time::format_description::parse("[hour]:[minute]:[second]").unwrap(),
                ));
            #[cfg(feature = "console")]
            {
                let filter = EnvFilter::from_default_env()
                    .add_directive("tokio=trace".parse().unwrap())
                    .add_directive("runtime=trace".parse().unwrap());
                let subscriber = tracing_subscriber::registry().with(fmt.with_filter(filter));
                let _ = subscriber.with(console_subscriber::spawn()).try_init();
            }
            #[cfg(not(feature = "console"))]
            {
                let _ = tracing_subscriber::registry()
                    .with(fmt.with_filter(EnvFilter::from_default_env()))
                    .try_init();
            }
        }
    }
}

/// Initialize the tracing system.
///
/// This uses the pretty display format to prioritize readability for developers.
/// Pretty logs will not get imported into the `stats` schema for reporting.
pub fn init_pretty_tracing() {
    init_tracing(StdoutFormat::Pretty);
}
