import type { DocumentReviewArtifact } from './types'

interface DocumentReviewSummary {
  kind: 'agreement' | 'supplemented' | 'differences' | 'unavailable'
  title: string
  description: string
}

export function summarizeDocumentReview(review: DocumentReviewArtifact): DocumentReviewSummary {
  if (review.error_message) {
    return {
      kind: 'unavailable',
      title: 'LLM cross-check unavailable',
      description: review.error_message,
    }
  }
  const relevantComparisons = review.comparisons.filter(
    (item) => item.status !== 'missing_in_both',
  )
  const reviewedFields = relevantComparisons.length
  const differentFields = relevantComparisons.filter((item) => item.status !== 'match').length
  const conflicts = relevantComparisons.filter((item) => item.status === 'different').length
  if (review.fallback_fields.length > 0 && conflicts === 0) {
    return {
      kind: 'supplemented',
      title: `LLM filled ${review.fallback_fields.length} missing ${review.fallback_fields.length === 1 ? 'field' : 'fields'}`,
      description:
        'The first extraction stays primary. Highlighted gaps use the second reading.',
    }
  }
  if (differentFields > 0) {
    return {
      kind: 'differences',
      title:
        conflicts > 0
          ? `Readings disagree on ${conflicts} ${conflicts === 1 ? 'field' : 'fields'}`
          : `LLM found ${differentFields} differences`,
      description:
        'The first extraction remains selected for conflicts. Review the evidence below.',
    }
  }
  return {
    kind: 'agreement',
    title: 'LLM cross-check agrees',
    description: `The second reading matched all ${reviewedFields} compared fields. Agreement does not prove accuracy.`,
  }
}
