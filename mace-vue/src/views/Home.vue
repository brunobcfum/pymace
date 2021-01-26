<template>
  <v-container >
    <v-row>
      <span v-if="isConnected">Connected</span>
    </v-row>
    <v-col justify="space-around" align="center">
      <img alt="Logo" src="../assets/logo.png">
      <div class="hello">

        <p>
          This is a WebApp GUI to interact with MACE - Mobile Ad-Hoc Computing Emulator<br>
          check out the
          <a href="https://github.com/brunobcfum/pymace" target="_blank" rel="noopener">MACE repository</a> for more information.
        </p>
      </div>
    </v-col>
  </v-container>
</template>

<script>
  export default {
    name: "Home",
    data: () => ({
      isConnected: false
    }),
    created() {
    },
    sockets: {
      // Fired when the server sends something on the "messageChannel" channel.
      messageChannel (data) {
        this.socketMessage = data
      },
      ponggg () {
        console.log("my pong")
      }
    },
    methods: {
      pingServer () {
        this.$socket.emit('teste', {data: 'I\'m connected!'});
        this.$socket.emit('pingServer', 'eu', 'PING!')
      }
    }
  }
</script>

<style>

</style>
