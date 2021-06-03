<template>
  <v-container class="elevation-2">
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
          <v-row>
            <v-col cols="2">
              <v-text-field
                dense
                v-model="grid_size"
                solo
                label="Grid size"
              ></v-text-field>
            </v-col>
            <v-col cols="10">
              <v-slider
                :min="25"
                class="pt-1"
                dense
                v-model="grid_size"
                label="Grid Size"
              ></v-slider>
            </v-col>
          </v-row>


        </v-col>
      </v-row>
    </v-form>
  </v-container>
</template>

<script>
export default {
  data () {
    return {
      file: [],
      value: [],
      grid_size: 50,
      radius_size: 120,
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
    grid_size: function () {
      this.$emit('grid_changed', this.grid_size)
    },
    radius_size: function () {
      this.$emit('range_changed', this.radius_size)
    }
  }
}
</script>

<style>

</style>