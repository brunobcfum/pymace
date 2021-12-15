<template>
  <div>
    <v-tabs vertical v-model="model">
      <v-tab v-for="net in networks" :key="net.id" :href="`#tab-${net.id}`">
        <v-icon left>
          mdi-access-point
        </v-icon>
        {{ net.name }}
      </v-tab>

      <v-tabs-items v-model="model">
        <v-tab-item v-for="net in networks" :key="net.id" :value="`tab-${net.id}`">
          <v-card flat width="100%">
            <v-card-text>
              <p>
                {{ net.description }}
              </p>

            </v-card-text>
          </v-card>
        </v-tab-item>
      </v-tabs-items>
    </v-tabs>
  </div>
</template>

<script>
export default {
  data () {
    return {
      model: 'tab-1',
      file: [],
      networks: [
        {
          id: 1,
          name: "Uma",
          description: "Descricao1"
        },
        {
          id: 2,
          name: "Duas",
          description: "Descricao2"
        },
        {
          id: 3,
          name: "Tres",
          description: "Descricao3"
        }
      ],
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