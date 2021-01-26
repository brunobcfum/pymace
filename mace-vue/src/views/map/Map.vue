<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <p>First marker is placed at {{ withPopup.lat }}, {{ withPopup.lng }}</p>
        <p>Center is at {{ currentCenter }} and the zoom is: {{ currentZoom }}</p>
        <v-btn @click="showLongText">
          Toggle long popup
        </v-btn>
        <v-btn @click="showMap = !showMap">
          Toggle map
        </v-btn>
      </v-col>
    </v-row>
    <v-row >
      <v-col >
        <div class="nodes-map">
        <l-map
            v-if="showMap"
            :zoom="zoom"
            :center="center"
            :options="mapOptions"
            @update:center="centerUpdate"
            @update:zoom="zoomUpdate"
            style="height:600px;"
          >
            <l-tile-layer
              :url="url"
              :attribution="attribution"
            />
          <l-marker :lat-lng="withPopup">
            <l-popup>
              <div @click="innerClick">
                I am a popup
                <p v-show="showParagraph">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque
                  sed pretium nisl, ut sagittis sapien. Sed vel sollicitudin nisi.
                  Donec finibus semper metus id malesuada.
                </p>
              </div>
            </l-popup>
          </l-marker>
          <l-marker :lat-lng="withTooltip">
            <l-tooltip :options="{ permanent: true, interactive: true }">
              <div @click="innerClick">
                I am a tooltip
                <p v-show="showParagraph">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque
                  sed pretium nisl, ut sagittis sapien. Sed vel sollicitudin nisi.
                  Donec finibus semper metus id malesuada.
                </p>
              </div>
            </l-tooltip>
          </l-marker>
        </l-map>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { latLng } from "leaflet";
import { LMap, LTileLayer, LMarker, LPopup, LTooltip } from "vue2-leaflet";
import "leaflet/dist/leaflet.css";


export default {
  name: "Example",
  components: {
    LMap,
    LTileLayer,
    LMarker,
    LPopup,
    LTooltip
  },
  data() {
    return {
      zoom: 18,
      center: latLng(43.56401772616047, 1.4813253222387137),
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution:
        '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      withPopup: latLng(43.56301772616047, 1.4813253222387137),
      withTooltip: latLng(43.56401772616047, 1.4812253222387137),
      currentZoom: 11.5,
      currentCenter: latLng(43.56401772616047, 1.4813253222387137),
      showParagraph: false,
      mapOptions: {
        zoomSnap: 0.5
      },
      showMap: true
    };
  },
  methods: {
    zoomUpdate(zoom) {
      this.currentZoom = zoom;
    },
    centerUpdate(center) {
      this.currentCenter = center;
    },
    showLongText() {
      this.showParagraph = !this.showParagraph;
    },
    innerClick() {
      alert("Click!");
    }
  }
}

</script>



