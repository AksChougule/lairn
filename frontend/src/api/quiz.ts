import { apiClient } from './client'
import type {
  CreateQuizSessionRequest,
  CreateQuizSessionResponse,
  HealthResponse,
  SessionListResponse,
  SessionSummaryResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from '../types/api'

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}

export async function createQuizSession(
  payload: CreateQuizSessionRequest,
): Promise<CreateQuizSessionResponse> {
  const { data } = await apiClient.post<CreateQuizSessionResponse>('/api/v1/quiz/sessions', payload)
  return data
}

export async function submitAnswer(
  sessionId: string,
  questionId: string,
  payload: SubmitAnswerRequest,
): Promise<SubmitAnswerResponse> {
  const { data } = await apiClient.post<SubmitAnswerResponse>(
    `/api/v1/quiz/sessions/${sessionId}/questions/${questionId}/answer`,
    payload,
  )
  return data
}

export async function getSessionSummary(sessionId: string): Promise<SessionSummaryResponse> {
  const { data } = await apiClient.get<SessionSummaryResponse>(`/api/v1/quiz/sessions/${sessionId}/summary`)
  return data
}

export async function listSessions(limit = 20, offset = 0): Promise<SessionListResponse> {
  const { data } = await apiClient.get<SessionListResponse>('/api/v1/quiz/sessions', {
    params: { limit, offset },
  })
  return data
}
