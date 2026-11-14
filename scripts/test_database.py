from app.database import get_supabase_client

supabase = get_supabase_client()

response = (
    supabase.table("contracts")
    .select("*")
    .limit(1)
    .execute()
)

print("Database connection successful!")
print("Query response:", response.data)