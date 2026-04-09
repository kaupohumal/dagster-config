<template>
  <div class="module-config">
    <div class="text-h6">json_mapper</div>
    <div
      v-for="(mapping, index) in mappings"
      :key="index"
      class="pair-row"
    >
      <div class="pair-field">
        <q-input
          label="Source"
          v-model="mapping.value"
        />
      </div>
      <div class="pair-field">
        <q-input
          label="Target"
          v-model="mapping.key"
        />
      </div>
      <div class="pair-action">
        <q-btn
          @click="mappings.splice(index, 1)"
          icon="close"
          color="negative"
          dense
          flat
        />
      </div>
    </div>
    <div>
      <q-btn
        @click="mappings.push(createEmptyPair(MAPPING_FIELDS))"
        icon="add"
        color="primary"
        class="q-mt-sm"
      />
    </div>
    <q-btn
      @click="applyConfig"
      label="Save"
      class="module-save-btn"
      color="primary"
    />
  </div>
</template>

<script setup lang="ts">

import {onMounted, ref} from "vue";
import {
  createEmptyPair,
  MAPPING_FIELDS,
  normalizePairList,
  type Mapping,
} from "components/models";
import {api} from "boot/axios";
import {useRoute} from "vue-router";
import {useQuasar} from "quasar";
import {getApiErrorMessage} from "../utils/errors";

const route = useRoute();
const $q = useQuasar();
const props = defineProps<{
  moduleIndex: number;
}>();

const apiEndpoint: string = `pipelines/${route.params.pipelineName as string}/modules/json_mapper/${props.moduleIndex}`;
const mappings = ref<Mapping[]>([createEmptyPair(MAPPING_FIELDS)]);

onMounted(async () => {
  await getModuleConfig()
})

const getModuleConfig = async () => {
  const res = await api.get(apiEndpoint);
  mappings.value = normalizePairList(res.data?.mappings, MAPPING_FIELDS);
}

const applyConfig = async () => {
  try {
    await api.patch(apiEndpoint, {
      'mappings': mappings.value,
    });

    $q.notify({
      type: 'positive',
      message: 'Saved json_mapper module changes.',
    });
  } catch (error: unknown) {
    $q.notify({
      type: 'negative',
      message: getApiErrorMessage(error, 'Failed to save json_mapper module changes.'),
    });
  }
}

</script>

<style scoped>
.module-config {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
}

.pair-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 8px;
}

.pair-field {
  flex: 1 1 0;
  min-width: 0;
}

.pair-action {
  flex: 0 0 auto;
  padding-top: 10px;
}

.module-save-btn {
  margin-top: auto;
  align-self: flex-end;
}
</style>

