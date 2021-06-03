<template>
  <v-navigation-drawer
    v-model="menu"
    app
    dark
    @transitionend="toggleMenu"
    src="@/assets/background.jpg"
  >
  <v-list dense>

    <v-list-item two-line @click="openHome">
      <v-list-item-title class="title">
        <span >mace-</span>
        <span class="font-weight-bold">vue</span>
      </v-list-item-title>
    </v-list-item>

    <v-divider></v-divider>
    <v-list-item @click="openObserver">
      <v-list-item-action>
          <v-icon>mdi-quadcopter</v-icon>
      </v-list-item-action>
      <v-list-item-content>
          <v-list-item-title>Live Observer</v-list-item-title>
      </v-list-item-content>
    </v-list-item>

    <v-list-item @click="openCreator">
      <v-list-item-action>
          <v-icon>mdi-lan</v-icon>
      </v-list-item-action>
      <v-list-item-content>
          <v-list-item-title>Topology Creator</v-list-item-title>
      </v-list-item-content>
    </v-list-item>

    <v-list-item @click="opendNetFlow">
      <v-list-item-action>
          <v-icon>mdi-lan</v-icon>
      </v-list-item-action>
      <v-list-item-content>
          <v-list-item-title>dNetFlow Creator</v-list-item-title>
      </v-list-item-content>
    </v-list-item>

    <v-list-item @click="openAbout">
      <v-list-item-action>
          <v-icon>mdi-help-circle</v-icon>
      </v-list-item-action>
      <v-list-item-content>
          <v-list-item-title>About this page</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
  </v-list>
  <template v-slot:append>

  </template>
  </v-navigation-drawer>
</template>

<script>

export default {
  data () {
    return {
      menu: false
    }
  },
  props: {
    drawer: Boolean
  },
  mounted () {
    this.menu = this.drawer
  },
  watch: {
    drawer () {
      this.menu = this.drawer
    }
  },
  methods: {
    toggleMenu () {
      if (this.drawer !== this.menu) {
        this.$emit('toggleMenu')
      }
    },
    openCreator () {
      this.$router.push({
        name: 'creator'
      }).catch(err => {
        if (err.name != "NavigationDuplicated") {
          throw err;
        }})
    },
    opendNetFlow () {
      this.$router.push({
        name: 'dnetflow'
      }).catch(err => {
        if (err.name != "NavigationDuplicated") {
          throw err;
        }})
    },
    openHome () {
      this.$router.push({
        name: 'home'
      }).catch(err => {
        if (err.name != "NavigationDuplicated") {
          throw err;
        }})
    },
    openObserver () {
      this.$router.push({
        name: 'observer'
      }).catch(err => {
        if (err.name != "NavigationDuplicated") {
          throw err;
        }})
    },
    openAbout () {
      this.$router.push({
        name: 'about'
      }).catch(err => {
        if (err.name != "NavigationDuplicated") {
          throw err;
        }})
    }
  }
}
</script>

<style>

</style>
