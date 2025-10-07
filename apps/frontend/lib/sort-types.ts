/**
 * Strongly typed enums for sorting experiences
 */

export enum SortField {
  DATE = 'date',
  RATING = 'rating',
  DURATION = 'duration',
  START_WEIGHT = 'startWeight',
  END_WEIGHT = 'endWeight',
  WEIGHT_CHANGE = 'weightChange',
  WEIGHT_LOSS_PERCENT = 'weightLossPercent',
  WEIGHT_LOSS_SPEED = 'weightLossSpeed',
  WEIGHT_LOSS_SPEED_PERCENT = 'weightLossSpeedPercent',
}

export enum SortDirection {
  ASC = 'asc',
  DESC = 'desc',
}

export type SortFieldType = `${SortField}`
export type SortDirectionType = `${SortDirection}`

/**
 * Sort field display names for UI
 */
export const SORT_FIELD_LABELS: Record<SortField, string> = {
  [SortField.DATE]: 'Date',
  [SortField.RATING]: 'Rating',
  [SortField.DURATION]: 'Duration',
  [SortField.START_WEIGHT]: 'Start Weight',
  [SortField.END_WEIGHT]: 'End Weight',
  [SortField.WEIGHT_CHANGE]: 'Weight Lost (lbs)',
  [SortField.WEIGHT_LOSS_PERCENT]: 'Weight Lost (%)',
  [SortField.WEIGHT_LOSS_SPEED]: 'Loss Speed (lbs/mo)',
  [SortField.WEIGHT_LOSS_SPEED_PERCENT]: 'Loss Speed (%/mo)',
}

/**
 * Sort direction tooltips
 */
export const SORT_DIRECTION_TOOLTIPS: Record<SortDirection, string> = {
  [SortDirection.ASC]: 'Sort ascending',
  [SortDirection.DESC]: 'Sort descending',
}
