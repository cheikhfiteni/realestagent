import { API_BASE_URL } from './config';
import CacheService from './cache';

export interface Job {
  id: string;
  name: string;
  last_updated: string;
  listing_count: number;
}

const cache = CacheService.getInstance();
const JOBS_CACHE_KEY = 'jobs';
const JOB_CACHE_KEY_PREFIX = 'job_';

export async function fetchJobs(): Promise<Job[]> {
  // Try to get from cache first
  const cachedJobs = cache.get<Job[]>(JOBS_CACHE_KEY);
  if (cachedJobs) return cachedJobs;

  // If not in cache, fetch from API
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    credentials: 'include',
  });

  if (!response.ok) throw new Error('Failed to fetch jobs');
  
  const jobs = await response.json();
  cache.set(JOBS_CACHE_KEY, jobs);
  return jobs;
}

export function getJob(jobId: string): Job | null {
  const jobs = cache.get<Job[]>(JOBS_CACHE_KEY);
  if (!jobs) return null;
  
  return jobs.find(job => job.id === jobId) || null;
}

export function invalidateJobsCache(): void {
  cache.invalidate(JOBS_CACHE_KEY);
  cache.invalidate(JOB_CACHE_KEY_PREFIX);
} 