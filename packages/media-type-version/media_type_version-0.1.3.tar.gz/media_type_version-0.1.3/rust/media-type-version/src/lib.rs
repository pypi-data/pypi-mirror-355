#![deny(missing_docs)]
#![deny(clippy::missing_docs_in_private_items)]
#![no_std]
// SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
// SPDX-License-Identifier: BSD-2-Clause
//! media-type-version - extract the format version from a media type string
//!
//! ## Overview
//!
//! The `media-type-version` library is designed to be used as the first step in
//! parsing structured data, e.g. configuration files, serialized classes, etc.
//! The caller extracts the media type string (e.g. a JSON `"mediaType": "..."` key) and
//! passes it in for parsing.
//! The caller then decides what to do with the extracted version information -
//! is this version supported, what fields are expected to be there, should any
//! extraneous fields produce errors, and so on.
//!
//! The main entry point is the [`extract`] function which is passed two parameters:
//! a [`Config`] object defining the expected media type prefix and suffix, and
//! a media type string to parse.
//! On success, it returns a [`Version`] object, basically a tuple of a major and
//! minor version numbers.
//!
//! ## Media type string format
//!
//! The media type string is expected to be in a `<prefix>.vX.Y<suffix>` format, with
//! a fixed prefix and suffix.
//! The prefix will usually be a vendor-specific media type.
//! The version part consists of two unsigned integer numbers.
//! The suffix, if used, may correspond to the file format.
//!
//! A sample media type string identifying a TOML configuration file for
//! a text-processing program could be
//! `vnd.ringlet.textproc.publync.config/publync.v0.2+toml`
//!
//! ## Crate features
//!
//! - `alloc` - enable the [`Error::into_owned_error`] method
//! - `facet-unstable` - [`Config`] and [`Version`] will derive from `Facet` so that
//!   they can be examined or serialized that way.
//!
//!   Note that the `facet-unstable` feature adds a pinned version dependency on
//!   whatever version of the `facet` crate is current at the time of release of
//!   the `media-type-version` crate!
//!   If this feature is activated, it is strongly recommended to have a pinned
//!   version dependency on `media-type-version` itself!

#![doc(html_root_url = "https://docs.rs/media-type-version/0.1.3")]
#![expect(clippy::pub_use, reason = "re-export common symbols")]

use core::str::FromStr as _;

use log::debug;

mod defs;

pub use defs::{Config, Error, Version};

#[cfg(feature = "alloc")]
pub use defs::OwnedError;

/// Extract the format version from a media type string.
///
/// # Errors
///
/// [`Error::NoPrefix`], [`Error::NoSuffix`], [`Error::NoVDot`] if
/// the media type string does not contain the required string parts at all.
///
/// [`Error::TwoComponentsExpected`] if the version part does not consist of
/// exactly two dot-separated components.
///
/// [`Error::UIntExpected`] if those components are not unsigned integers.
#[inline]
pub fn extract<'data>(
    cfg: &'data Config<'data>,
    value: &'data str,
) -> Result<Version, Error<'data>> {
    debug!(
        "Parsing a media type string '{value}', expecting prefix '{prefix}' and suffix '{suffix}'",
        prefix = cfg.prefix(),
        suffix = cfg.suffix()
    );
    let no_prefix = value
        .strip_prefix(cfg.prefix())
        .ok_or_else(|| Error::NoPrefix(value, cfg.prefix()))?;
    let no_suffix = no_prefix
        .strip_suffix(cfg.suffix())
        .ok_or_else(|| Error::NoSuffix(value, cfg.suffix()))?;
    let no_vdot = no_suffix
        .strip_prefix(".v")
        .ok_or(Error::NoVDot(no_suffix))?;
    let (first, second) = {
        let mut parts_it = no_vdot.split('.');
        let first = parts_it.next().ok_or(Error::TwoComponentsExpected(value))?;
        let second = parts_it.next().ok_or(Error::TwoComponentsExpected(value))?;
        if parts_it.next().is_some() {
            return Err(Error::TwoComponentsExpected(value));
        }
        (first, second)
    };
    let major = u32::from_str(first).map_err(|err| Error::UIntExpected(value, first, err))?;
    let minor = u32::from_str(second).map_err(|err| Error::UIntExpected(value, second, err))?;
    Ok(Version::from((major, minor)))
}

#[cfg(test)]
mod tests {
    extern crate alloc;

    use alloc::format;
    use alloc::string::String;

    use eyre::WrapErr as _;
    use facet_testhelpers::test;

    #[cfg(feature = "facet-unstable")]
    use facet_pretty::FacetPretty as _;

    use crate::{Config, Error, Version};

    /// The prefix and suffix to use for testing.
    static CFG: Config<'_> = Config::from_parts("this/and", "+that");

    #[cfg(feature = "facet-unstable")]
    fn pretty_res(res: &Result<Version, Error<'_>>) -> String {
        match *res {
            Ok(ref ver) => format!("OK: {ver}", ver = ver.pretty()),
            Err(ref err) => format!("Error: {err}"),
        }
    }

    #[cfg(not(feature = "facet-unstable"))]
    fn pretty_res(res: &Result<Version, Error<'_>>) -> String {
        match *res {
            Ok(ref ver) => format!(
                "OK: Version {{ major: {major}, minor: {minor} }}",
                major = ver.major(),
                minor = ver.minor(),
            ),
            Err(ref err) => format!("Error: {err}"),
        }
    }

    /// Make sure [extract][crate::extract] fails on invalid prefix.
    #[test]
    fn extract_fail_no_prefix() {
        let res = crate::extract(&CFG, "nothing");
        assert!(
            matches!(res, Err(Error::NoPrefix(_, _))),
            "expected Error::NoPrefix, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails on invalid suffix.
    #[test]
    fn extract_fail_no_suffix() {
        let res = crate::extract(&CFG, "this/andnothing");
        assert!(
            matches!(res, Err(Error::NoSuffix(_, _))),
            "expected Error::NoSuffix, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails on missing "v.".
    #[test]
    fn extract_fail_no_vdot() {
        let res = crate::extract(&CFG, "this/andnothing+that");
        assert!(
            matches!(res, Err(Error::NoVDot(_))),
            "expected Error::NoVDot, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails if no two components.
    #[test]
    fn extract_fail_two_expected() {
        let res = crate::extract(&CFG, "this/and.vnothing+that");
        assert!(
            matches!(res, Err(Error::TwoComponentsExpected(_))),
            "expected Error::TwoComponentsExpected, got {res}",
            res = pretty_res(&res)
        );
    }

    /// Make sure [extract][crate::extract] fails if not unsigned integers.
    #[test]
    fn extract_fail_uint_expected() {
        let res_first = crate::extract(&CFG, "this/and.va.42+that");
        assert!(
            matches!(res_first, Err(Error::UIntExpected(_, _, _))),
            "expected Error::UIntExpected, got {res_first}",
            res_first = pretty_res(&res_first)
        );

        let res_second = crate::extract(&CFG, "this/and.v42.+that");
        assert!(
            matches!(res_second, Err(Error::UIntExpected(_, _, _))),
            "expected Error::UIntExpected, got {res_second}",
            res_second = pretty_res(&res_second)
        );
    }

    /// Make sure [extract][crate::extract] succeeds on trivial correct data.
    #[test]
    fn extract_ok() {
        let ver = crate::extract(&CFG, "this/and.v616.42+that").context("extract")?;
        assert_eq!(ver.as_tuple(), (616, 42));
    }
}
