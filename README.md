

## Media storage

For local development, uploaded media files are stored on the filesystem
and persisted via a Docker volume.

In a production environment, media files would typically be stored in
object storage (e.g. S3-compatible storage) and served via a CDN.
This is intentionally out of scope for this assignment.
