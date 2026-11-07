# Publisher decisions before public distribution

This file is a preparation note, **not a license grant**. It deliberately does not choose MIT, Apache or another license for the author's new integration code or branding.

Before the first public release, record the following decisions:

| Component | Decision to record |
| --- | --- |
| New skill instructions and integration scripts | Rights holder, authorized license and copyright notice |
| STCA logo and other new visual assets | Rights holder and permitted use or brand policy |
| Public candidate fixture and aggregate validation records | Permission to distribute and applicable terms |
| Original polymer-stca implementation and pretrained artifacts | Applicable upstream license and any additional written distribution authorization |

The exact pinned upstream LICENSE is already retained in `THIRD_PARTY_NOTICES.md`. That upstream notice names The University of Tokyo and University College London as copyright holders and includes commercial-use and redistribution restrictions. An author identity alone does not rewrite those terms. If appropriate permissions already exist, document their actual scope; this note does not assert that new permission is necessarily absent.

After deciding the new integration license, add its final text as the repository's `LICENSE`, set the relevant license metadata where supported, and remove or move this preparation note out of the public release. Preserve the upstream notice even if the new integration uses a different license. Do not put unverified license identifiers in `CITATION.cff`, a plugin manifest or archive metadata.
