import type { Topic } from '../types/api'

export const topicOptions: Array<{ value: Topic; label: string }> = [
  { value: 'Machine Learning technical concepts', label: 'Machine Learning' },
  { value: 'Deep Learning technical concepts', label: 'Deep Learning' },
  { value: 'Statistics', label: 'Statistics' },
  { value: 'Generative AI', label: 'Generative AI' },
  { value: 'MLOps technical concepts', label: 'MLOps' },
  { value: 'Agentic AI technical concepts', label: 'Agentic AI' },
  { value: 'API technical concepts', label: 'API' },
  { value: 'LLM and Foundational Model concepts', label: 'LLM & FM' },
]

const topicLabelMap: Record<Topic, string> = topicOptions.reduce(
  (acc, item) => {
    acc[item.value] = item.label
    return acc
  },
  {} as Record<Topic, string>,
)

export function getTopicLabel(topic: Topic): string {
  return topicLabelMap[topic] ?? topic
}
