#!/usr/bin/env python3
"""
Quick Supabase Connection Diagnostic Tool
Run this to identify your specific connection issue.
"""

import sys

print("🔍 SUPABASE CONNECTION DIAGNOSTIC")
print("=" * 70)

# Step 1: Check if required packages are installed
print("\n[1/6] Checking required packages...")
try:
    import psycopg2

    print("✅ psycopg2 is installed")
except ImportError:
    print("❌ psycopg2 is NOT installed")
    print("   Fix: pip install psycopg2-binary")
    sys.exit(1)

try:
    from sqlalchemy import create_engine, text

    print("✅ SQLAlchemy is installed")
except ImportError:
    print("❌ SQLAlchemy is NOT installed")
    print("   Fix: pip install sqlalchemy")
    sys.exit(1)

# Step 2: Check .env file
print("\n[2/6] Checking .env file...")
try:
    from dotenv import load_dotenv
    import os

    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("❌ DATABASE_URL not found in .env file")
        print("   Fix: Add DATABASE_URL to your .env file")
        sys.exit(1)

    print("✅ DATABASE_URL found in .env")

    # Parse and display (hide password)
    if "@" in db_url:
        parts = db_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split("://")[1]
            if ":" in user_pass:
                username = user_pass.split(":")[0]
                print(f"   Username: {username}")
                print(f"   Host: {parts[1] if len(parts) > 1 else 'unknown'}")

except ImportError:
    print("⚠️  python-dotenv not installed (optional)")
    db_url = input("\n   Please paste your DATABASE_URL: ").strip()

# Step 3: Validate URL format
print("\n[3/6] Validating connection string format...")

required_parts = ["postgresql://", "supabase.com", ":"]
issues = []

if not db_url.startswith("postgresql://"):
    issues.append("❌ Must start with 'postgresql://'")
else:
    print("✅ Correct protocol (postgresql://)")

if "supabase.com" not in db_url and "supabase.co" not in db_url:
    issues.append("⚠️  Doesn't contain 'supabase.com' - are you sure this is Supabase?")
else:
    print("✅ Supabase domain detected")

if "pooler.supabase.com" in db_url:
    print("✅ Using connection pooler (recommended)")
    expected_port = "6543"
    if f":{expected_port}/" in db_url:
        print(f"✅ Correct pooler port ({expected_port})")
    else:
        issues.append(f"⚠️  Expected port {expected_port} for pooler")
elif "db." in db_url and "supabase.co" in db_url:
    print("ℹ️  Using direct connection")
    expected_port = "5432"
    if f":{expected_port}/" in db_url:
        print(f"✅ Correct direct port ({expected_port})")
    else:
        issues.append(f"⚠️  Expected port {expected_port} for direct connection")

if "sslmode=require" not in db_url:
    issues.append("⚠️  Missing 'sslmode=require' parameter (recommended)")
    print("⚠️  SSL mode not specified - will add it")
    separator = "&" if "?" in db_url else "?"
    db_url = f"{db_url}{separator}sslmode=require"
else:
    print("✅ SSL mode configured")

# Step 4: Test network connectivity
print("\n[4/6] Testing network connectivity...")
try:
    import socket

    # Extract host from URL
    host = db_url.split("@")[1].split(":")[0] if "@" in db_url else None

    if host:
        print(f"   Testing connection to {host}...")
        socket.setdefaulttimeout(5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Determine port
        port = 6543 if "pooler" in db_url else 5432

        try:
            s.connect((host, port))
            s.close()
            print(f"✅ Can reach {host}:{port}")
        except socket.error as e:
            print(f"❌ Cannot reach {host}:{port}")
            print(f"   Error: {e}")
            issues.append(f"Network connectivity issue to {host}:{port}")
    else:
        print("⚠️  Could not extract host from URL")

except Exception as e:
    print(f"⚠️  Network test skipped: {e}")

# Step 5: Test database connection with psycopg2
print("\n[5/6] Testing connection with psycopg2...")
try:
    # Parse connection string
    from urllib.parse import urlparse

    parsed = urlparse(db_url)

    # Extract components
    username = parsed.username
    password = parsed.password
    hostname = parsed.hostname
    port = parsed.port or 5432
    database = parsed.path.lstrip("/")

    print(f"   Connecting to {hostname}:{port}...")
    print(f"   Database: {database}")
    print(f"   Username: {username}")

    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port,
        connect_timeout=10,
        sslmode="require",
    )

    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ Connection successful!")
    print(f"   PostgreSQL: {version[:60]}...")

    cursor.close()
    conn.close()

    print("\n🎉 SUCCESS! Your connection string is working!")
    print("\nYou can now use this in your .env file:")
    print(f"\nDATABASE_URL={db_url}")

except psycopg2.OperationalError as e:
    error_msg = str(e)
    print(f"❌ Connection failed: {error_msg[:200]}")

    # Diagnose specific errors
    if "password authentication failed" in error_msg.lower():
        print("\n🔍 DIAGNOSIS: Wrong password!")
        print("   Solutions:")
        print("   1. Go to Supabase Dashboard > Settings > Database")
        print("   2. Reset your database password")
        print("   3. Update DATABASE_URL in .env with the new password")
        print("   4. Note: Use DATABASE password, not account password!")

    elif "connection refused" in error_msg.lower():
        print("\n🔍 DIAGNOSIS: IP might be banned or network issue!")
        print("   Solutions:")
        print("   1. Go to Supabase Dashboard > Settings > Database")
        print("   2. Scroll down and click 'Unban IP'")
        print("   3. Wait 30 seconds and try again")
        print("   4. Check if you can reach Supabase servers")

    elif "timeout" in error_msg.lower():
        print("\n🔍 DIAGNOSIS: Connection timeout!")
        print("   Solutions:")
        print("   1. Check your internet connection")
        print("   2. Check if firewall is blocking port 6543 or 5432")
        print("   3. Try using a VPN if in a restricted network")

    elif "name or service not known" in error_msg.lower():
        print("\n🔍 DIAGNOSIS: Cannot resolve hostname!")
        print("   Solutions:")
        print("   1. Check if your connection string is correct")
        print("   2. Verify project reference in URL")
        print("   3. Check DNS settings")

    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {type(e).__name__}: {e}")
    sys.exit(1)

# Step 6: Test with SQLAlchemy
print("\n[6/6] Testing connection with SQLAlchemy...")
try:
    engine = create_engine(db_url, echo=False)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ SQLAlchemy connection successful!")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nYour configuration is correct. You can now run your application.")

except Exception as e:
    print(f"❌ SQLAlchemy test failed: {e}")
    sys.exit(1)

# Summary
if issues:
    print("\n⚠️  WARNINGS:")
    for issue in issues:
        print(f"   {issue}")

print("\n✅ Diagnostic complete!")
