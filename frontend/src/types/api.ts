export type Topic =
  | 'Machine Learning technical concepts'
  | 'Deep Learning technical concepts'
  | 'Statistics'
  | 'Generative AI'
  | 'MLOps technical concepts'
  | 'Agentic AI technical concepts'
  | 'API technical concepts'
  | 'LLM and Foundational Model concepts'

export type Difficulty = 'easy' | 'medium' | 'hard'
export type QuestionType = 'mcq' | 'short-answer' | 'mixed'

export interface CreateQuizSessionRequest {
  topics: Topic[]
  difficulty: Difficulty
  question_type: QuestionType
  num_questions: number
}

export interface QuizQuestionPublic {
  id: string
  order_index: number
  type: QuestionType
  topic_tags: Topic[]
  difficulty: Difficulty
  prompt: string
  options: string[] | null
}

export interface CreateQuizSessionResponse {
  session_id: string
  created_at: string
  config: CreateQuizSessionRequest
  questions: QuizQuestionPublic[]
}

export interface SubmitAnswerRequest {
  answer?: string
  option_index?: number
}

export interface SubmitAnswerResponse {
  is_correct: boolean
  correct_answer: string
  explanation: string
  why_others_wrong: string[]
  normalized_user_answer: string
}

export interface SessionScore {
  correct: number
  total: number
}

export interface TopicScore {
  topic: Topic
  correct: number
  total: number
}

export interface SessionSummaryResponse {
  session_id: string
  score: SessionScore
  by_topic: TopicScore[]
  created_at: string
  completed_at: string | null
}

export interface SessionListItem {
  session_id: string
  created_at: string
  completed_at: string | null
  score: SessionScore
  config: CreateQuizSessionRequest
}

export interface SessionListResponse {
  limit: number
  offset: number
  items: SessionListItem[]
}

export interface HealthResponse {
  status: string
  ollama: {
    reachable: boolean
    model: string
  }
}
