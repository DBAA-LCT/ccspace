<template>
  <div>
    <div class="section-head">
      <div>
        <h2>管理员</h2>
        <p>管理后台账号和权限</p>
      </div>
      <t-button theme="primary" shape="round" @click="openDialog()">添加管理员</t-button>
    </div>

    <div class="table-card">
      <t-table row-key="id" :data="admins" :columns="adminColumns" :loading="loading" bordered>
        <template #role="{ row }">
          <span class="badge" :class="row.role === 'owner' ? 'badge-info' : 'badge-success'">
            {{ row.role === 'owner' ? '店主' : '店员' }}
          </span>
        </template>
        <template #createdAt="{ row }">{{ formatTime(row.createdAt) }}</template>
        <template #actions="{ row }">
          <t-space>
            <t-button size="small" variant="text" @click="openDialog(row)">编辑</t-button>
            <t-button size="small" variant="text" theme="danger" @click="remove(row)" v-if="row.role !== 'owner'">删除</t-button>
          </t-space>
        </template>
      </t-table>
    </div>

    <div class="section-head" style="margin-top: 32px">
      <div>
        <h2>修改密码</h2>
        <p>修改当前管理员的登录密码</p>
      </div>
    </div>
    <div class="card" style="max-width: 480px">
      <t-form :data="pwdForm" label-width="80px" @submit="changePassword">
        <t-form-item label="原密码" name="oldPassword">
          <t-input v-model="pwdForm.oldPassword" type="password" placeholder="当前密码" />
        </t-form-item>
        <t-form-item label="新密码" name="newPassword">
          <t-input v-model="pwdForm.newPassword" type="password" placeholder="至少6位" />
        </t-form-item>
        <t-form-item>
          <t-button theme="primary" type="submit" :loading="pwdLoading" shape="round">修改密码</t-button>
        </t-form-item>
      </t-form>
    </div>

    <t-dialog v-model:visible="dialogVisible" :header="editingId ? '编辑管理员' : '添加管理员'" width="min(480px, 90vw)" :footer="false">
      <t-form :data="form" label-width="80px" @submit="submit">
        <t-form-item label="账号" name="username">
          <t-input v-model="form.username" :disabled="!!editingId" placeholder="登录账号" />
        </t-form-item>
        <t-form-item label="密码" name="password" v-if="!editingId">
          <t-input v-model="form.password" type="password" placeholder="至少6位" />
        </t-form-item>
        <t-form-item label="昵称" name="name">
          <t-input v-model="form.name" placeholder="显示名称" />
        </t-form-item>
        <t-form-item label="角色" name="role">
          <t-select v-model="form.role">
            <t-option value="staff" label="店员" />
            <t-option value="owner" label="店主" />
          </t-select>
        </t-form-item>
        <div class="dialog-footer">
          <t-button theme="default" @click="dialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="submitting" shape="round">保存</t-button>
        </div>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { request, formatTime } from "../utils/api";
import { adminColumns } from "../utils/constants";
import { MessagePlugin, DialogPlugin } from "tdesign-vue-next";

const admins = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const editingId = ref("");
const submitting = ref(false);
const pwdLoading = ref(false);

function emptyForm() {
  return { username: "", password: "", name: "", role: "staff" };
}
const form = reactive(emptyForm());
const pwdForm = reactive({ oldPassword: "", newPassword: "" });

async function load() {
  loading.value = true;
  try {
    admins.value = await request("/api/admin/admins");
  } catch (error) {
    if (error.message.includes("仅店主")) {
      admins.value = [];
    } else {
      MessagePlugin.error(error.message);
    }
  } finally {
    loading.value = false;
  }
}

function openDialog(row) {
  editingId.value = row?.id || "";
  Object.assign(form, row ? { ...row } : emptyForm());
  dialogVisible.value = true;
}

async function submit() {
  submitting.value = true;
  try {
    if (editingId.value) {
      await request(`/api/admin/admins/${editingId.value}`, {
        method: "PUT",
        body: JSON.stringify({ name: form.name, role: form.role })
      });
    } else {
      await request("/api/admin/admins", {
        method: "POST",
        body: JSON.stringify(form)
      });
    }
    dialogVisible.value = false;
    await load();
    MessagePlugin.success("已保存");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    submitting.value = false;
  }
}

async function remove(row) {
  const confirm = DialogPlugin.confirm({
    header: "确认删除",
    body: `确定要删除管理员「${row.name}」吗？`,
    theme: "danger",
    onConfirm: async () => {
      try {
        await request(`/api/admin/admins/${row.id}`, { method: "DELETE" });
        await load();
        MessagePlugin.success("已删除");
      } catch (error) {
        MessagePlugin.error(error.message);
      }
      confirm.hide();
    },
    onClose: () => confirm.hide()
  });
}

async function changePassword() {
  if (!pwdForm.oldPassword || !pwdForm.newPassword) {
    MessagePlugin.warning("请填写完整");
    return;
  }
  pwdLoading.value = true;
  try {
    await request("/api/admin/change-password", {
      method: "POST",
      body: JSON.stringify(pwdForm)
    });
    pwdForm.oldPassword = "";
    pwdForm.newPassword = "";
    MessagePlugin.success("密码已修改");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    pwdLoading.value = false;
  }
}

onMounted(load);
</script>
