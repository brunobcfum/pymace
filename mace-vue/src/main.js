import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import store from './store'
import router from './router'
import VueSocketIOExt from 'vue-socket.io-extended'
import io from 'socket.io-client'
import VueKonva from 'vue-konva'

import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png')
});

Vue.config.productionTip = false

Vue.use(VueKonva)


const socket = io('http://localhost:5000/sim');
Vue.use(VueSocketIOExt, socket);

new Vue({
  vuetify,
  store,
  router,
  render: h => h(App)
}).$mount('#app')
