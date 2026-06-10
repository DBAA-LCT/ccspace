import { createRouter, createWebHistory } from "vue-router";
import { token } from "../utils/api";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login.vue")
  },
  {
    path: "/",
    component: () => import("../layouts/AppShell.vue"),
    children: [
      { path: "", name: "Dashboard", component: () => import("../views/Dashboard.vue") },
      { path: "products", name: "Products", component: () => import("../views/Products.vue") },
      { path: "orders", name: "Orders", component: () => import("../views/Orders.vue") },
      { path: "parcels", name: "Parcels", component: () => import("../views/Parcels.vue") }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  if (!token.value && to.name !== "Login") {
    return { name: "Login" };
  }
  if (token.value && to.name === "Login") {
    return { name: "Dashboard" };
  }
});

export default router;
