<template>
  <div class="card">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">
      <span v-if="prefix" class="stat-unit">{{ prefix }}</span>
      {{ displayValue }}
      <span v-if="suffix" class="stat-unit">{{ suffix }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  prefix: { type: String, default: "" },
  suffix: { type: String, default: "" }
});

const displayValue = computed(() => {
  if (typeof props.value === "number") return props.value.toLocaleString();
  return props.value;
});
</script>
