"""
Job store - placeholder.

For the spine-first build, this is empty. Once the real backend logic lands,
this module will provide a Redis-backed dict-like interface for tracking
async job state (pending / running / done / failed) and results.

Keeping the file present in the spine means imports won't break when we
plug in the real implementation.
"""