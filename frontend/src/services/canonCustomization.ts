import api from '../lib/api';
import type {
  CanonAnnotation,
  CanonAnnotationCreateRequest,
  CanonAnnotationFilters,
  CanonCustomizationProfile,
  CanonCustomizationProfileCreateRequest,
  CanonCustomizationProfileUpdateRequest,
} from '../types/canonCustomization';
import type { CanonGenerationPacket } from '../types/storyGeneration';

export async function getCanonAnnotations(
  projectId: string,
  filters?: CanonAnnotationFilters,
): Promise<CanonAnnotation[]> {
  const response = await api.get('/v1/canon/annotations', {
    params: {
      project_id: projectId,
      target_kind: filters?.target_kind,
      target_id: filters?.target_id,
    },
  });
  return response.data;
}

export async function createCanonAnnotation(
  request: CanonAnnotationCreateRequest,
): Promise<CanonAnnotation> {
  const response = await api.post('/v1/canon/annotations', request);
  return response.data;
}

export async function deleteCanonAnnotation(projectId: string, annotationId: string): Promise<void> {
  await api.delete(`/v1/canon/annotations/${annotationId}`, {
    params: { project_id: projectId },
  });
}

export async function getCanonProfiles(projectId: string): Promise<CanonCustomizationProfile[]> {
  const response = await api.get('/v1/canon/profiles', { params: { project_id: projectId } });
  return response.data;
}

export async function createCanonProfile(
  request: CanonCustomizationProfileCreateRequest,
): Promise<CanonCustomizationProfile> {
  const response = await api.post('/v1/canon/profiles', request);
  return response.data;
}

export async function updateCanonProfile(
  profileId: string,
  projectId: string,
  updates: CanonCustomizationProfileUpdateRequest,
): Promise<CanonCustomizationProfile> {
  const response = await api.patch(`/v1/canon/profiles/${profileId}`, updates, {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function deleteCanonProfile(projectId: string, profileId: string): Promise<void> {
  await api.delete(`/v1/canon/profiles/${profileId}`, {
    params: { project_id: projectId },
  });
}

export async function previewCanonProfilePacket(
  projectId: string,
  profileId: string,
): Promise<CanonGenerationPacket> {
  const response = await api.post(`/v1/canon/profiles/${profileId}/packet-preview`, null, {
    params: { project_id: projectId },
  });
  return response.data;
}
