<template>
  <v-app-bar app dark dense>
    <v-app-bar-nav-icon @click="toggleMenu"></v-app-bar-nav-icon>
    <v-toolbar-title v-if="!drawer" class="grey--text">
      <span>mace</span>
      <span class="font-weight-bold">vue</span>
    </v-toolbar-title>
    <v-spacer></v-spacer>
    <v-toolbar-items>
      <v-switch
        class="pt-3"
        v-model="$vuetify.theme.dark"
        label="Dark"
      ></v-switch>
    </v-toolbar-items>
  </v-app-bar>
</template>

<script>
export default {
  data () {
    return {

    }
  },
  methods: {
    toggleMenu () {
      this.$emit('toggleMenu')
    }
  },
  props: {
    drawer: Boolean
  }
}
</script>

<style>

</style>
