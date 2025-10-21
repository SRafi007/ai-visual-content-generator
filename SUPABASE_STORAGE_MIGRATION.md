# Supabase Storage Migration Guide

This document explains how to use Supabase Storage for image persistence in production.

## Why Supabase Storage?

**Problem**: Streamlit Cloud has an ephemeral filesystem - files are deleted on app restart.

**Solution**: Supabase Storage provides persistent, CDN-backed image storage with public URLs.

## Setup Instructions

### 1. Configure Environment Variables

Update your `.env` file (or Streamlit Cloud secrets):

```env
# Storage
STORAGE_TYPE=supabase  # Change from 'local' to 'supabase'

# Supabase Storage
SUPABASE_URL=https://uqmijmgophetotqgonns.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_BUCKET_NAME=arbor_images
```

### 2. Create Supabase Bucket

Run the setup script to create the bucket and folder structure:

```bash
python scripts/setup_supabase_storage.py
```

This will:
- Create the `arbor_images` bucket (public access)
- Create `images/` and `thumbnails/` folders
- Verify your credentials

### 3. Verify Installation

Make sure the `supabase` package is installed:

```bash
pip install supabase>=2.0.0
```

It's already in `requirements.txt`, so it will be installed automatically.

## How It Works

### StorageService Updates

The `StorageService` class now supports both local and Supabase storage:

```python
from src.services.storage_service import StorageService

storage = StorageService()

# Save image (automatically uses Supabase if STORAGE_TYPE=supabase)
image_url, thumb_url = storage.save_image_with_thumbnail(
    image_data=image_bytes,
    generation_id=generation_id
)

# Returns:
# - Local: file paths (e.g., "./data/images/uuid.png")
# - Supabase: public URLs (e.g., "https://...supabase.co/storage/v1/object/public/arbor_images/images/uuid.png")
```

### Folder Structure in Supabase

```
arbor_images/
├── images/
│   ├── {generation_id}.png
│   └── ...
└── thumbnails/
    ├── {generation_id}_thumb.png
    └── ...
```

### Fallback Behavior

If Supabase upload fails, the service automatically falls back to local storage with a warning.

## Streamlit Cloud Deployment

### Setting Secrets

In Streamlit Cloud Dashboard → Settings → Secrets:

```toml
[env]
STORAGE_TYPE = "supabase"
SUPABASE_URL = "https://uqmijmgophetotqgonns.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_BUCKET_NAME = "arbor_images"

# Other secrets...
DATABASE_URL = "postgresql://..."
REDIS_URL = "rediss://..."
GEMINI_API_KEY = "..."
IMAGEN_API_KEY = "..."
```

## Supabase Bucket Configuration

### Create Bucket Manually (Alternative)

If you prefer to create the bucket manually:

1. Go to Supabase Dashboard → Storage
2. Click "New Bucket"
3. Name: `arbor_images`
4. Public bucket: **Yes** (for CDN access)
5. Click "Create Bucket"

### Set Bucket Policies (Important!)

To allow public read access:

1. Go to Storage → Policies
2. Add policy for `arbor_images`:

```sql
-- Allow public read access
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'arbor_images');

-- Allow authenticated uploads (using anon key)
CREATE POLICY "Authenticated Upload"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'arbor_images');
```

## Testing

### Local Testing

Set `STORAGE_TYPE=supabase` in `.env` and run:

```bash
streamlit run src/ui/app.py
```

Generate an image and verify:
- Image uploads to Supabase
- URL is returned (starts with `https://`)
- Image is accessible via URL

### Verify in Supabase Dashboard

1. Go to Supabase Dashboard → Storage → arbor_images
2. Check that `images/` and `thumbnails/` folders contain your generated images
3. Click on an image to view it

## Migration Notes

### Database Schema

The database already stores URLs as `TEXT` fields:
- `generated_image_url` (TEXT)
- `thumbnail_url` (TEXT)

No schema changes needed! Both file paths and URLs work.

### Existing Local Images

Local images won't be automatically migrated. Options:

1. **Keep both**: Local for development, Supabase for production
2. **Migrate manually**: Upload local images to Supabase using the API
3. **Start fresh**: Only new generations use Supabase

## Benefits

✅ **Persistent storage** - Images survive app restarts
✅ **CDN delivery** - Fast global access
✅ **Scalable** - No filesystem limits
✅ **Already integrated** - Using Supabase for database
✅ **Cost-effective** - Free tier: 1GB storage, 2GB bandwidth

## Troubleshooting

### Images not uploading

- Check `SUPABASE_ANON_KEY` is correct
- Verify bucket is public
- Check bucket policies allow uploads
- Review logs for error messages

### Images not accessible

- Verify bucket is marked as "Public"
- Check URL format: `https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}`
- Test URL in browser

### Fallback to local storage

If you see "Falling back to local storage" warnings:
- Check Supabase credentials
- Verify network connectivity
- Review Supabase project status

## Cost Considerations

**Supabase Free Tier**:
- 1 GB storage
- 2 GB bandwidth/month
- Unlimited API requests

**Estimated usage**:
- Average image: 200 KB
- Average thumbnail: 20 KB
- ~4,500 images fit in 1 GB

For higher usage, upgrade to Supabase Pro ($25/month for 100 GB).

## Next Steps

1. Run setup script: `python scripts/setup_supabase_storage.py`
2. Update `.env` with `STORAGE_TYPE=supabase`
3. Test locally
4. Deploy to Streamlit Cloud with secrets configured
5. Generate test image to verify end-to-end flow

---

**Created**: 2025-10-22
**Updated**: 2025-10-22
