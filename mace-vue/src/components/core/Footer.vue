<template>
  <v-footer
    dense
    inset
    padless
    app
    class="font-weight-this; overline"
  >
    <v-col
      cols="6"
    >
      <div v-if="isConnected">Conneceted to server</div>
      <div v-if="!isConnected">Disconneceted from server</div>
    </v-col>
    <v-col
      class="text-right"
      cols="6"
    >
      © BrunoCF {{ new Date().getFullYear() }}
    </v-col>
  </v-footer>
</template>

<script>
export default {
  name: "Footer",
  data: () => ({
    isConnected: false
  }),
  sockets: {
    connect () {
      // Fired when the socket connects.
      this.isConnected = true
    },
    disconnect () {
      this.isConnected = false
    }
  }
}
</script>

<style>

</style>
