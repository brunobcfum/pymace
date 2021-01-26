import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import store from './store'
import router from './router'
import VueSocketIO from 'vue-socket.io'
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

Vue.use(new VueSocketIO({
  debug: false,
  connection: 'http://127.0.0.1:5000/sim'
}))

new Vue({
  vuetify,
  store,
  router,
  render: h => h(App)
}).$mount('#app')
