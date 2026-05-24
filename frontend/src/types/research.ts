export interface ResearchItem {
  item_id: string;
  project_id: string;
  title: string;
  content: string;
  source_url: string | null;
  source_type: string;
  genre_tags: string[];
  status: string;
  citations: string[];
  created_at: string;
  updated_at: string;
}

export interface ResearchItemCreateRequest {
  project_id: string;
  title: string;
  content: string;
  source_url?: string | null;
  source_type?: string;
  status?: string;
  genre_tags?: string[];
  citations?: string[];
}

export interface ResearchItemUpdateRequest {
  title?: string;
  content?: string;
  source_url?: string | null;
  source_type?: string;
  genre_tags?: string[];
  status?: string;
  citations?: string[];
}

export interface ResearchItemListResponse {
  project_id: string;
  items: ResearchItem[];
  meta: Record<string, string>;
}
