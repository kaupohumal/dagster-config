<template>
  <q-card flat bordered class="q-mt-lg">
    <q-card-section class="row items-center q-col-gutter-md">
      <div class="col">
        <div class="text-subtitle1">Schedule</div>
        <div class="text-caption text-grey-7">Optional cron schedule for this pipeline.</div>
      </div>
      <div class="col-auto">
        <q-toggle v-model="isEnabled" label="Enabled" :disable="loading" />
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section class="q-gutter-md">
      <div v-if="isEnabled" class="q-gutter-md">
        <q-select
          v-model="mode"
          label="Timing"
          :options="modeOptions"
          emit-value
          map-options
          :disable="loading"
        />

        <div v-if="mode === 'interval'" class="row q-col-gutter-md">
          <q-select
            class="col-12 col-sm-6"
            v-model="intervalMinutes"
            label="Run every"
            :options="intervalOptions"
            emit-value
            map-options
            :disable="loading"
          />
        </div>

        <div v-else-if="mode === 'hourly'" class="row q-col-gutter-md">
          <q-select
            class="col-12 col-sm-6"
            v-model="hourlyMinute"
            label="Minute"
            :options="minuteOptions"
            emit-value
            map-options
            :disable="loading"
          />
        </div>

        <div v-else-if="mode === 'daily'" class="row q-col-gutter-md">
          <q-select
            class="col-12 col-sm-6"
            v-model="dailyHour"
            label="Hour"
            :options="hourOptions"
            emit-value
            map-options
            :disable="loading"
          />
          <q-select
            class="col-12 col-sm-6"
            v-model="dailyMinute"
            label="Minute"
            :options="minuteOptions"
            emit-value
            map-options
            :disable="loading"
          />
        </div>

        <div v-else-if="mode === 'weekly'" class="row q-col-gutter-md">
          <q-select
            class="col-12 col-sm-4"
            v-model="weeklyDay"
            label="Day"
            :options="weekdayOptions"
            emit-value
            map-options
            :disable="loading"
          />
          <q-select
            class="col-12 col-sm-4"
            v-model="weeklyHour"
            label="Hour"
            :options="hourOptions"
            emit-value
            map-options
            :disable="loading"
          />
          <q-select
            class="col-12 col-sm-4"
            v-model="weeklyMinute"
            label="Minute"
            :options="minuteOptions"
            emit-value
            map-options
            :disable="loading"
          />
        </div>

        <q-input
          v-else
          v-model="customCron"
          label="Cron expression"
          hint="Format: minute hour day-of-month month day-of-week"
          :disable="loading"
        />

        <q-banner rounded class="bg-blue-1 text-primary">
          <div><strong>Preview:</strong> {{ humanReadable }}</div>
          <div class="text-caption">Cron: <code>{{ normalizedDraftCron }}</code></div>
        </q-banner>
      </div>

      <q-banner v-else rounded class="bg-grey-2 text-grey-8">
        No schedule. This pipeline only runs when manually triggered.
      </q-banner>

      <div class="row justify-end">
        <q-btn
          color="primary"
          :label="isEnabled ? 'Save schedule' : 'Remove schedule'"
          :disable="loading || !canSubmit"
          :loading="loading"
          @click="emitSave"
        />
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

type ScheduleMode = 'interval' | 'hourly' | 'daily' | 'weekly' | 'custom';

const props = withDefaults(
  defineProps<{
    cron: string | null;
    loading?: boolean;
  }>(),
  {
    loading: false,
  },
);

const emit = defineEmits<{
  save: [string | null];
}>();

const mode = ref<ScheduleMode>('interval');
const isEnabled = ref(false);
const intervalMinutes = ref('5');
const hourlyMinute = ref('0');
const dailyHour = ref('0');
const dailyMinute = ref('0');
const weeklyDay = ref('1');
const weeklyHour = ref('0');
const weeklyMinute = ref('0');
const customCron = ref('*/5 * * * *');

const intervalOptions = [1, 5, 10, 15, 30, 60].map((value) => ({
  label: value === 60 ? '60 minutes (hourly)' : `${value} minutes`,
  value: String(value),
}));

const modeOptions = [
  { label: 'Every X minutes', value: 'interval' },
  { label: 'Hourly', value: 'hourly' },
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Custom cron', value: 'custom' },
] as const;

const minuteOptions = Array.from({ length: 60 }, (_, value) => ({
  label: String(value).padStart(2, '0'),
  value: String(value),
}));

const hourOptions = Array.from({ length: 24 }, (_, value) => ({
  label: String(value).padStart(2, '0'),
  value: String(value),
}));

const weekdayLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const weekdayOptions = weekdayLabels.map((label, value) => ({ label, value: String(value) }));

const pad2 = (value: string) => String(Number(value)).padStart(2, '0');

const draftCron = computed(() => {
  if (!isEnabled.value) {
    return null;
  }

  if (mode.value === 'interval') {
    const minutes = Number(intervalMinutes.value);
    if (!Number.isInteger(minutes) || minutes <= 0) {
      return null;
    }
    return minutes === 60 ? '0 * * * *' : `*/${minutes} * * * *`;
  }

  if (mode.value === 'hourly') {
    return `${Number(hourlyMinute.value)} * * * *`;
  }

  if (mode.value === 'daily') {
    return `${Number(dailyMinute.value)} ${Number(dailyHour.value)} * * *`;
  }

  if (mode.value === 'weekly') {
    return `${Number(weeklyMinute.value)} ${Number(weeklyHour.value)} * * ${Number(weeklyDay.value)}`;
  }

  const trimmed = customCron.value.trim();
  return trimmed.length > 0 ? trimmed : null;
});

const normalizedIncomingCron = computed(() => {
  const trimmed = props.cron?.trim();
  return trimmed && trimmed.length > 0 ? trimmed : null;
});

const normalizedDraftCron = computed(() => {
  const trimmed = draftCron.value?.trim();
  return trimmed && trimmed.length > 0 ? trimmed : 'Not set';
});

const humanReadable = computed(() => {
  if (!isEnabled.value) {
    return 'No schedule';
  }

  if (mode.value === 'interval') {
    return `Every ${intervalMinutes.value} minute(s)`;
  }

  if (mode.value === 'hourly') {
    return `Every hour at minute ${pad2(hourlyMinute.value)}`;
  }

  if (mode.value === 'daily') {
    return `Every day at ${pad2(dailyHour.value)}:${pad2(dailyMinute.value)}`;
  }

  if (mode.value === 'weekly') {
    return `Every ${weekdayLabels[Number(weeklyDay.value)]} at ${pad2(weeklyHour.value)}:${pad2(weeklyMinute.value)}`;
  }

  return 'Custom cron expression';
});

const canSubmit = computed(() => {
  if (!isEnabled.value) {
    return normalizedIncomingCron.value !== null;
  }

  const current = draftCron.value?.trim();
  return Boolean(current && current.length > 0 && current !== normalizedIncomingCron.value);
});

function applyCronToForm(cron: string | null): void {
  const value = cron?.trim();
  if (!value) {
    isEnabled.value = false;
    mode.value = 'interval';
    intervalMinutes.value = '5';
    customCron.value = '*/5 * * * *';
    return;
  }

  isEnabled.value = true;
  customCron.value = value;

  let match = value.match(/^\*\/(\d{1,2})\s+\*\s+\*\s+\*\s+\*$/);
  if (match) {
    const every = match[1];
    if (!every) {
      mode.value = 'custom';
      return;
    }
    mode.value = 'interval';
    intervalMinutes.value = every;
    return;
  }

  match = value.match(/^(\d{1,2})\s+\*\s+\*\s+\*\s+\*$/);
  if (match) {
    const minuteRaw = match[1];
    if (!minuteRaw) {
      mode.value = 'custom';
      return;
    }
    if (Number(minuteRaw) < 0 || Number(minuteRaw) > 59) {
      mode.value = 'custom';
      return;
    }
    mode.value = 'hourly';
    hourlyMinute.value = minuteRaw;
    return;
  }

  match = value.match(/^(\d{1,2})\s+(\d{1,2})\s+\*\s+\*\s+\*$/);
  if (match) {
    const minuteRaw = match[1];
    const hourRaw = match[2];
    if (!minuteRaw || !hourRaw) {
      mode.value = 'custom';
      return;
    }
    const minute = Number(minuteRaw);
    const hour = Number(hourRaw);
    if (minute >= 0 && minute <= 59 && hour >= 0 && hour <= 23) {
      mode.value = 'daily';
      dailyMinute.value = minuteRaw;
      dailyHour.value = hourRaw;
      return;
    }
  }

  match = value.match(/^(\d{1,2})\s+(\d{1,2})\s+\*\s+\*\s+([0-6])$/);
  if (match) {
    const minuteRaw = match[1];
    const hourRaw = match[2];
    const dayRaw = match[3];
    if (!minuteRaw || !hourRaw || !dayRaw) {
      mode.value = 'custom';
      return;
    }
    const minute = Number(minuteRaw);
    const hour = Number(hourRaw);
    if (minute >= 0 && minute <= 59 && hour >= 0 && hour <= 23) {
      mode.value = 'weekly';
      weeklyMinute.value = minuteRaw;
      weeklyHour.value = hourRaw;
      weeklyDay.value = dayRaw;
      return;
    }
  }

  mode.value = 'custom';
}

const emitSave = () => {
  emit('save', draftCron.value);
};

watch(
  () => props.cron,
  (nextCron) => {
    applyCronToForm(nextCron);
  },
  { immediate: true },
);
</script>


