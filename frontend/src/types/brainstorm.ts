export interface BrainstormItem {
  item_id: string;
  project_id: string;
  content: string;
  item_type: 'IDEA' | 'CHARACTER' | 'SETTING' | 'PLOT_POINT' | 'THEME' | 'QUESTION';
  state: 'KEEP' | 'DISCARD' | 'PARK';
  tags: string[];
  cluster_id: string | null;
  promoted_to: string | null;
  promoted_at: string | null;
  created_at: string;
}

export interface BrainstormItemCreateRequest {
  content: string;
  item_type?: 'IDEA' | 'CHARACTER' | 'SETTING' | 'PLOT_POINT' | 'THEME' | 'QUESTION';
  state?: 'KEEP' | 'DISCARD' | 'PARK';
  tags?: string[];
  cluster_id?: string | null;
}

export interface BrainstormClusterRequest {
  item_ids: string[];
}
