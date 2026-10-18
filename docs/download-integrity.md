# When a download comparison fails

This guide is for contributors running the repository tests. If the CLI rejects your own CSV, start with the [input-error guide](input-errors.md). A CSV input error and an archive/source mismatch are different conditions.

## Identify the failed check

Some tests compare extracted example files with their corresponding source copies byte for byte. A mismatch says those bytes differ. It does not, by itself, show that the cost formula is wrong, that a user download failed, or that any private experiment produced an accepted result.

Check which file and revision the test compares. A historical release ZIP and later main-branch source can intentionally contain different versions. Compare the matching artifacts, rather than treating the newest source as the expected content of every old release.

## Account for checkout line endings

Git can normalize text line endings in its index and use different endings in a working checkout. LF and CRLF can display as the same lines while containing different bytes. Git's [attributes documentation](https://git-scm.com/docs/gitattributes) explains the `text` and `eol` settings.

The repository's [scoped repair](https://github.com/ahmadreza-smdi/ai-workflow-cost/commit/f2fa5af5203de52216271cb1c1697c610a25b011) added LF rules for seven specific worked-example text paths after a Windows archive/source comparison failed. That change preserved the CLI and example ZIP bytes. It was not a change to the cost arithmetic, and it did not modify old tagged release assets.

## Reconcile the files, then rerun

Keep local work and private ledgers intact. Inspect the named source file, its applicable `.gitattributes` rules and the revision being tested. A separate checkout of the intended revision can help distinguish local edits or checkout conversion from the committed files without overwriting your working copy.

Do not delete the comparison or normalize every archive member just to obtain a pass. The worked-example comparison requires exact bytes; the paired-ledger package explicitly normalizes CRLF for its fixed text members. Do not extend that normalization to other files just to obtain a pass; broad conversion can hide a different file or version.

From the repository root, using Python 3.10 or newer:

```sh
python -B -m unittest discover -s tests -v
```

A successful suite is evidence about its cases and environment. It does not certify every computer, real-world acceptance judgement, or completeness of recorded costs.

[Return to the project](../README.md)
