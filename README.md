# kcwt-meta-images (code only — not deployed)

Tiny static+API host for short-lived 1080×1350 JPEGs that Meta Graph fetches.

## Env (names only)

| Name | Purpose |
| --- | --- |
| `KCWT_META_IMAGES_SECRET` | Shared secret for `POST /upload` and `DELETE /i/<id>.jpg` |
| `KCWT_META_IMAGES_PUBLIC_BASE` | Public https origin returned in upload JSON (e.g. `https://….up.railway.app`) |
| `PORT` | Listen port (Railway sets) |
| `DATA_DIR` | File store (default `/data`) |

## Routes

- `POST /upload` + `X-Auth-Secret` → `{"id","url"}` for `/i/<64 hex>.jpg`
- `GET /i/<64 hex>.jpg` → image or 404
- `DELETE /i/<64 hex>.jpg` + `X-Auth-Secret` → 204
- Anything else → 404 (no listing)

Do **not** deploy until `KCWT_META_PAGE_TOKEN` health is confirmed and Atlas says go.
