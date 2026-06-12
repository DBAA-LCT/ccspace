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
      { path: "parcels", name: "Parcels", component: () => import("../views/Parcels.vue") },
      { path: "admins", name: "Admins", component: () => import("../views/Admins.vue") },
      { path: "preview", name: "Preview", component: () => import("../views/Preview.vue") },
      { path: "delivery-plan", name: "DeliveryPlan", component: () => import("../views/DeliveryPlan.vue") },
      { path: "promotions", name: "Promotions", component: () => import("../views/Promotions.vue") }
    ]
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/"
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
