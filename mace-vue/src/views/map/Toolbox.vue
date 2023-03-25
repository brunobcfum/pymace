<template>
    <v-form>
      <v-row
        align="center"
        justify="space-around">
        <v-col>
          <v-row
          align="center"
          justify="space-around">
            <v-col cols="4">
              <v-file-input
                dense
                solo
                v-model="file"
                accept="application/json"
                label="File input"
              ></v-file-input>
            </v-col>
            <v-col cols="8" class="pb-9">
              <v-btn
                @click="load"
                small
                elevation="3"
                color="primary"
                class="ma-2"
              >
                <v-icon left>
                  mdi-folder-open
                </v-icon>
                Load
              </v-btn>
              <v-btn
                small
                color="primary"
                elevation="3"
                @click="save"
                class="ma-2"
              >
                <v-icon left>
                  mdi-content-save
                </v-icon>
                Save
              </v-btn>
              <v-btn
                @click="clear"
                small
                color="error"
                class="ma-2"
                elevation="3"
              >
                <v-icon left>
                  mdi-recycle
                </v-icon>
                Clear
              </v-btn>
            </v-col>
          </v-row>
          <v-row
            align="center"
            justify="space-around">
            <v-chip class="elevation-3" label>Lat={{ position.lat  | to_float}}</v-chip>
            <v-chip class="elevation-3" label>Long={{ position.long | to_float}}</v-chip>
          </v-row>
        </v-col>
        <v-col>
          <v-card class="pa-2">
            <v-radio-group v-model="node_type">
            <template v-slot:label>
                <div>Select node type:</div>
            </template>
            <v-row>
              <v-col>
                <v-radio value="uav">
                  <template v-slot:label>
                  <div>UAV</div>
                  </template>
                </v-radio>
                <v-radio value="antenna">
                  <template v-slot:label>
                  <div>Antenna</div>
                  </template>
                </v-radio>
                <v-radio value="edge_server">
                  <template v-slot:label>
                  <div>Edge Server</div>
                  </template>
                </v-radio>
              </v-col>
              <v-col>
                <v-radio value="smartphone">
                  <template v-slot:label>
                  <div>Smartphone</div>
                  </template>
                </v-radio>
                <v-radio value="iot">
                  <template v-slot:label>
                  <div>IoT Device</div>
                  </template>
                </v-radio>
              </v-col>
            </v-row>
            </v-radio-group>
          </v-card>
        </v-col>
        <v-col>
          <v-row>
            <v-col cols="2">
              <v-text-field
                v-model="radius_size"
                solo
                dense
                label="Radius"
              ></v-text-field>
            </v-col>
            <v-col cols="10">
              <v-slider
                class="pt-1"
                dense
                v-model="radius_size"
                label="Radius"
                :max="255"
              ></v-slider>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-form>
</template>

<script>
export default {
  data () {
    return {
      file: [],
      value: [],
      radius_size: 120,
      node_type: "uav"
    }
  },
  methods: {
    load () {
      if (this.file !== '') {
        this.$emit('load', this.file) 
      }
    },
    save () {
      this.$emit('save')
    },
    clear () {
      this.$emit('clear')
    }
  },
  watch: {
    radius_size: function () {
      this.$emit('range_changed', this.radius_size)
    },
    node_type: function () {
      this.$emit('node_type', this.node_type)
    }
  },
  filters: {
    to_float: function (number) {
      return parseFloat(number).toFixed(6)
    }
  },
  props: {
    position: Object,
  }
}
</script>

<style>

</style>