-- Supabase Database Schema for agtOS Auth
-- Run this in the Supabase SQL editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    subscription_status TEXT DEFAULT 'beta' CHECK (subscription_status IN ('beta', 'free', 'pro', 'enterprise')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Invite codes table
CREATE TABLE IF NOT EXISTS public.invite_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT UNIQUE NOT NULL,
    created_by UUID REFERENCES public.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    max_uses INTEGER,
    used_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Invite usage tracking
CREATE TABLE IF NOT EXISTS public.invite_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invite_code_id UUID NOT NULL REFERENCES public.invite_codes(id),
    user_id UUID NOT NULL REFERENCES public.users(id),
    used_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    UNIQUE(invite_code_id, user_id)
);

-- Auth tokens for offline access
CREATE TABLE IF NOT EXISTS public.auth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id),
    access_token TEXT UNIQUE NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_invite_codes_code ON public.invite_codes(code);
CREATE INDEX IF NOT EXISTS idx_invite_codes_active ON public.invite_codes(is_active);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON public.auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_access_token ON public.auth_tokens(access_token);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invite_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invite_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_tokens ENABLE ROW LEVEL SECURITY;

-- Policies for users table
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Policies for invite_codes (public read for validation)
CREATE POLICY "Anyone can read active invite codes" ON public.invite_codes
    FOR SELECT USING (is_active = true);

-- Policies for auth_tokens
CREATE POLICY "Users can manage own tokens" ON public.auth_tokens
    FOR ALL USING (auth.uid() = user_id);

-- Functions
CREATE OR REPLACE FUNCTION public.validate_and_use_invite_code(
    p_code TEXT,
    p_user_id UUID,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_invite_id UUID;
    v_is_valid BOOLEAN;
BEGIN
    -- Find and lock the invite code
    SELECT id INTO v_invite_id
    FROM public.invite_codes
    WHERE code = p_code
        AND is_active = true
        AND (expires_at IS NULL OR expires_at > NOW())
        AND (max_uses IS NULL OR used_count < max_uses)
    FOR UPDATE;

    IF v_invite_id IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if already used by this user
    IF EXISTS (
        SELECT 1 FROM public.invite_usage
        WHERE invite_code_id = v_invite_id AND user_id = p_user_id
    ) THEN
        RETURN FALSE;
    END IF;

    -- Record usage
    INSERT INTO public.invite_usage (invite_code_id, user_id, ip_address, user_agent)
    VALUES (v_invite_id, p_user_id, p_ip_address, p_user_agent);

    -- Increment usage count
    UPDATE public.invite_codes
    SET used_count = used_count + 1
    WHERE id = v_invite_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert default invite codes
INSERT INTO public.invite_codes (code, metadata, expires_at, max_uses) VALUES
    ('AGTOS-DEV-2025', '{"type": "developer", "never_expires": true}'::jsonb, NULL, NULL),
    ('BETA-EARLY-2025', '{"type": "beta", "batch": 1}'::jsonb, '2025-04-01'::timestamptz, 100),
    ('BETA-SPRING-2025', '{"type": "beta", "batch": 2}'::jsonb, '2025-07-01'::timestamptz, 500)
ON CONFLICT (code) DO NOTHING;