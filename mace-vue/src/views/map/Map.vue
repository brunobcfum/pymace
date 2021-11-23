<template>
  <v-container fluid>
    <v-row>
      <Toolbox
        v-bind:position="position"
        v-on:node_type="node_type_change"
        v-on:range_changed="update_range"
        v-on:save="save"
        v-on:load="load"
        v-on:clear="clear"
      />  
    </v-row>
    <v-row >
      <v-col >
        <div class="nodes-map">
        <l-map
            :zoom="zoom"
            :center="center"
            :options="mapOptions"
            @update:center="centerUpdate"
            @update:zoom="zoomUpdate"
            style="height:600px;"
            @mousemove="updateCoordinates"
            @click="add_node"
          >
            <l-tile-layer
              :url="url"
              :attribution="attribution"
            />
            <div
              v-for="node in nodes"
              :key="node.id"
            >
              <l-marker
                :draggable=drag
                :lat-lng="node.pos"
                :icon="node.icon"
                @dragend="handleDragend(node,$event)"
                @click="toggle(node)"
                >
                <l-tooltip :options="{ permanent: false, interactive: false }">
                  <div >
                    Node: {{node.id}}
                  </div>
                </l-tooltip> 
                <l-popup>
                  <v-card
                    dark
                    class="ma-2 d-flex flex-column"
                    max-width="600"
                    min-width="200"
                    max-height="400"
                    min-height="100"
                    outlined
                    elevation="3"
                  > 
                    <v-system-bar color="indigo" window>
                      <span>Node: {{ node.id }}</span>
                      <v-spacer></v-spacer>
                      <v-icon
                        @click="delete_node(node)"
                      >
                        mdi-delete-empty
                      </v-icon>
                    </v-system-bar>
                    <v-text-field
                      v-model="node.label"
                      solo
                      dense
                      label="Filled"
                      clearable
                    ></v-text-field>
                    <v-text-field
                      class="ml-5 mr-5"
                      label="Radio range"
                      type="number"
                      v-model="node.range"
                      placeholder="Range"
                    ></v-text-field>
                    <span class="caption font-weight-thin">Position:({{node.x}},{{node.y}})</span>
                    <span class="caption font-weight-thin">Type: {{node.type}}</span>

                    <v-spacer></v-spacer>
                    <v-divider></v-divider>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn light x-small>Update</v-btn>
                    </v-card-actions>
                  </v-card>
                </l-popup>
              </l-marker>
              <l-circle
                :lat-lng="node.pos"
                :radius="node.range | to_int"
                color="blue"
              />
            </div>
        </l-map>
        </div>
      </v-col>
    </v-row>
    <v-row> 
      <v-col>
        <div>Icons made by <a href="https://www.flaticon.com/authors/srip" title="srip">srip</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
        <div>Icons made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
        <div>Icons made by <a href="https://www.flaticon.com/authors/pause08" title="Pause08">Pause08</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { latLng } from "leaflet";
import L from 'leaflet';
import { LMap, LTileLayer, LMarker, LPopup, LTooltip, LCircle } from "vue2-leaflet";
import "leaflet/dist/leaflet.css";
import Toolbox from '@/views/map/Toolbox'

export default {
  name: "Example",
  components: {
    LMap,
    LTileLayer,
    LMarker,
    LPopup,
    LTooltip,
    LCircle,
    Toolbox
  },
  data() {
    return {
      // TODO: Radius is in meters!!
      importFile: '',
      range: 120,
      current_node_type: 'uav',
      icons: {
        uav: L.icon({
          iconUrl: require('@/assets/uav.png'),
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        }),
        antenna: L.icon({
          iconUrl: require('@/assets/antenna.png'),
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        }),
        edge_server: L.icon({
          iconUrl: require('@/assets/cloud.png'),
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        }),
        smartphone: L.icon({
          iconUrl: require('@/assets/smartphone.png'),
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        }),
        iot: L.icon({
          iconUrl: require('@/assets/iot.png'),
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        })
      },
      drag: true,
      zoom: 17,
      position: {
        lat: 0,
        long: 0
      },
      nodes: [],
      center: latLng(43.56401772616047, 1.4813253222387137),
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      currentCenter: latLng(43.56401772616047, 1.4813253222387137),
      mapOptions: {
        scrollWheelZoom: false,
        zoomSnap: 0.5
      }
    };
  },
  methods: {
    delete_node (node) {
      this.nodes.splice(node.id, 1)
      for (let i = node.id; i < this.nodes.length; i++) {
        this.nodes[i].id = i
      }
      const data = JSON.stringify(this.nodes)
      localStorage.setItem('map_nodes', data)
    },
    save () {
      const blob = new Blob([JSON.stringify(this.list, null, 2)], {type: 'text/json'})
      const e = document.createEvent('MouseEvents')
      const a = document.createElement('a')
      a.download = this.filename
      a.href = window.URL.createObjectURL(blob)
      a.dataset.downloadurl = ['text/json', a.download, a.href].join(':')
      e.initEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null)
      a.dispatchEvent(e)
    },
    load (file) {
      var reader = new FileReader()
      reader.onload = (file) => {
        this.list = JSON.parse(file.target.result)
        var data = JSON.stringify(this.list)
        localStorage.setItem('map_nodes', data)
      }
      reader.readAsText(file)
    },
    clear () {
      this.nodes = []
      this.importFile = ''
      const data = JSON.stringify(this.nodes)
      localStorage.setItem('map_nodes', data)
    },
    toggle(node) {
      node.show =  !node.show
    },
    handleDragend (node, ev) {
      node.pos = latLng(ev.target._latlng.lat, ev.target._latlng.lng)
      node.lat = ev.target._latlng.lat
      node.long = ev.target._latlng.lng
      node.x = ev.sourceTarget._newPos.x
      node.y = ev.sourceTarget._newPos.y
      const data = JSON.stringify(this.nodes)
      localStorage.setItem('map_nodes', data)
      // console.log(ev)
    },
    updateCoordinates(ev) {
      this.position.lat = ev.latlng.lat
      this.position.long = ev.latlng.lng
      // console.log(ev.latlng)
    },
    add_node(ev) {
      var node = {
        id: this.nodes.length,
        label:"node"+this.nodes.length,
        lat: ev.latlng.lat,
        long: ev.latlng.lng,
        x: ev.layerPoint.x,
        y: ev.layerPoint.y,
        pos: latLng(ev.latlng.lat, ev.latlng.lng),
        icon: this.icons[this.current_node_type],
        show: true,
        range: this.range,
        type: this.current_node_type
      }
      this.nodes.push(node)
      var data = JSON.stringify(this.nodes)
      localStorage.setItem('map_nodes', data)
      // console.log(node)
    },
    zoomUpdate(zoom) {
      this.currentZoom = zoom;
    },
    centerUpdate(center) {
      this.currentCenter = center;
    },
    node_type_change(type) {
      this.current_node_type = type
      const data = JSON.stringify(this.nodes)
      localStorage.setItem('map_nodes', data)
    },
    update_range (range) {
      this.range = range
    }
  },
  mounted () {
    this.$nextTick(() => {
        this.nodes = JSON.parse(localStorage.getItem('map_nodes')) || []
    })
  },
  filters: {
    to_int: function (number) {
      return parseInt(number,10)
    }
  }
}

</script>