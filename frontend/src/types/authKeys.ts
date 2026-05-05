export interface ApiKeyInfo {
  key_prefix: string;
  name: string;
  permissions: string[];
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}
