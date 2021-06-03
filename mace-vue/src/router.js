import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import Creator from './views/creator/Creator.vue'
import dNetFlow from './views/dnetflow/dNetFlow.vue'
import Observer from './views/observer/Observer.vue'
import NotFound from './components/core/NotFound.vue'
import About from './components/core/About.vue'

Vue.use(Router)

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/creator',
      name: 'creator',
      component: Creator
    },
    {
      path: '/dnetflow',
      name: 'dnetflow',
      component: dNetFlow
    },
    {
      path: '/about',
      name: 'about',
      component: About
    },
    {
      path: '/observer',
      name: 'observer',
      component: Observer
    },
    { path: '*', component: NotFound }
  ]
})
