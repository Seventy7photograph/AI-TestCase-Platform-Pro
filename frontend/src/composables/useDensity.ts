import { ref, watchEffect } from "vue";

export type Density = "compact" | "cozy" | "relaxed";

const STORAGE_KEY = "impeccable.density";
const VALID: Density[] = ["compact", "cozy", "relaxed"];

function initial(): Density {
  const stored = localStorage.getItem(STORAGE_KEY) as Density | null;
  return stored && VALID.includes(stored) ? stored : "cozy";
}

const density = ref<Density>(initial());

watchEffect(() => {
  document.documentElement.dataset.density = density.value;
  localStorage.setItem(STORAGE_KEY, density.value);
});

export function useDensity() {
  return {
    density,
    setDensity: (next: Density) => {
      density.value = next;
    },
  };
}
