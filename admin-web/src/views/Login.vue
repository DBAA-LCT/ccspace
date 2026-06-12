<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand-row">
        <div class="brand-mark">CC</div>
        <div>
          <div class="brand-title">CCspace 管理台</div>
          <div class="brand-sub">商品、订单、快递代收配送统一管理</div>
        </div>
      </div>
      <t-form :data="loginForm" label-width="0" @submit="login">
        <t-form-item name="username">
          <t-input v-model="loginForm.username" placeholder="账号" clearable />
        </t-form-item>
        <t-form-item name="password">
          <t-input v-model="loginForm.password" :type="showPwd ? 'text' : 'password'" placeholder="密码" clearable>
            <template #suffix>
              <span class="pwd-toggle" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁' }}</span>
            </template>
          </t-input>
        </t-form-item>
        <t-form-item name="apiBase">
          <t-input v-model="apiBaseInput" placeholder="API 地址" clearable />
        </t-form-item>
        <t-form-item>
          <t-button theme="primary" type="submit" block :loading="loading" shape="round">
            登录
          </t-button>
        </t-form-item>
      </t-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { apiBase, setApiBase, setToken, request } from "../utils/api";
import { MessagePlugin } from "tdesign-vue-next";

const router = useRouter();
const loading = ref(false);
const showPwd = ref(false);
const apiBaseInput = ref(apiBase.value);

const loginForm = reactive({
  username: "",
  password: ""
});

async function login() {
  if (!loginForm.username || !loginForm.password) {
    MessagePlugin.warning("请输入账号和密码");
    return;
  }
  loading.value = true;
  try {
    setApiBase(apiBaseInput.value);
    const data = await request("/api/admin/login", {
      method: "POST",
      body: JSON.stringify(loginForm)
    });
    setToken(data.token);
    router.push("/");
    MessagePlugin.success("登录成功");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    loading.value = false;
  }
}
</script>
