<template>
  <q-layout view="lHh Lpr lFf">

    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title @click="router.push('/pipelines')">
          Dagster Pipeline Configurator
        </q-toolbar-title>
        <q-tabs shrink>
          <q-tab
            name="pipelines"
            label="Pipelines"
            @click="router.push('/pipelines')"
          />
        </q-tabs>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view/>
    </q-page-container>

  </q-layout>
</template>

<script setup lang="ts">

import {useRouter} from "vue-router";

const router = useRouter();
</script>
