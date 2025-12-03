/**
 * Chart Data Aggregation Composable
 *
 * Aggregates events into time-series data for visualization.
 */

import { ref, computed, type Ref } from 'vue';
import type { HookEvent, ChartDataPoint } from '../types';

export type TimeRange = '1m' | '2m' | '3m' | '5m' | '10m';

const TIME_RANGES: Record<TimeRange, { buckets: number; interval: number }> = {
  '1m': { buckets: 60, interval: 1000 },      // 60 × 1s
  '2m': { buckets: 120, interval: 1000 },     // 120 × 1s => 2 minutes
  '3m': { buckets: 60, interval: 3000 },      // 60 × 3s
  '5m': { buckets: 60, interval: 5000 },      // 60 × 5s
  '10m': { buckets: 60, interval: 10000 },    // 60 × 10s
};

export function useChartData(events: Ref<HookEvent[]>) {
  // Default to 2 minutes for live-chart behaviour
  const timeRange = ref<TimeRange>('2m');

  const chartData = computed<ChartDataPoint[]>(() => {
    const config = TIME_RANGES[timeRange.value];
    const now = Date.now();
    const startTime = now - (config.buckets * config.interval);

    // Initialize buckets
    const buckets: ChartDataPoint[] = [];
    for (let i = 0; i < config.buckets; i++) {
      buckets.push({
        timestamp: startTime + (i * config.interval),
        count: 0,
        eventTypes: {},
        sessions: {}
      });
    }

    // Fill buckets with events
    for (const event of events.value) {
      const eventTime = event.timestamp || 0;
      if (eventTime < startTime) continue;

      const bucketIndex = Math.floor((eventTime - startTime) / config.interval);
      if (bucketIndex >= 0 && bucketIndex < buckets.length) {
        const bucket = buckets[bucketIndex];
        bucket.count++;
        bucket.eventTypes[event.hook_event_type] = (bucket.eventTypes[event.hook_event_type] || 0) + 1;
        bucket.sessions[event.session_id] = (bucket.sessions[event.session_id] || 0) + 1;
      }
    }

    return buckets;
  });

  const maxCount = computed(() => {
    return Math.max(1, ...chartData.value.map(d => d.count));
  });

  function setTimeRange(range: TimeRange) {
    timeRange.value = range;
  }

  return {
    chartData,
    maxCount,
    timeRange,
    setTimeRange,
    TIME_RANGES
  };
}
