import { ref, shallowRef } from "vue";

import { ApiError } from "@/api";

export function useAsync<TArgs extends unknown[], TResult>(
  task: (...args: TArgs) => Promise<TResult>,
) {
  const data = shallowRef<TResult | null>(null);
  const error = ref<ApiError | null>(null);
  const loading = ref(false);
  const ran = ref(false);

  async function run(...args: TArgs): Promise<TResult | null> {
    loading.value = true;
    error.value = null;
    try {
      const result = await task(...args);
      data.value = result;
      ran.value = true;
      return result;
    } catch (err) {
      error.value =
        err instanceof ApiError
          ? err
          : new ApiError(err instanceof Error ? err.message : "未知错误");
      return null;
    } finally {
      loading.value = false;
    }
  }

  return { data, error, loading, ran, run };
}
