import { createClient } from '@supabase/supabase-js'

// Both are injected at build time by Vite. The anon key is designed to be
// public - it identifies the project and carries no privileges beyond what
// Supabase's own rules allow - so shipping it in the bundle is expected.
// The service_role key is the one that must never appear here.
const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

/** False until the project's URL and anon key are configured. */
export const isSupabaseConfigured = Boolean(url && anonKey)

// Null rather than a half-built client, so the UI can show a setup message
// instead of failing on the first auth call.
export const supabase = isSupabaseConfigured ? createClient(url, anonKey) : null
