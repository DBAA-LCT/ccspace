<template>
  <div>
    <div class="section-head">
      <div>
        <h2>管理员</h2>
        <p>管理后台账号和权限</p>
      </div>
      <t-space>
        <t-button theme="default" variant="outline" shape="round" @click="openPwdDialog">修改密码</t-button>
        <t-button theme="primary" shape="round" @click="openDialog()">添加管理员</t-button>
      </t-space>
    </div>

    <div class="filter-bar">
      <t-input v-model="searchQ" placeholder="搜索用户名、昵称..." clearable style="width: 220px" @enter="load(1)" />
    </div>

    <div class="table-card">
      <t-table row-key="id" :data="pagedAdmins" :columns="adminColumns" :loading="loading" bordered>
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
      <div class="table-footer" v-if="filteredAdmins.length > pageSize">
        <t-pagination v-model="page" :total="filteredAdmins.length" :page-size="pageSize" show-jumper />
      </div>
    </div>

    <!-- 添加/编辑管理员 dialog -->
    <t-dialog v-model:visible="dialogVisible" :header="editingId ? '编辑管理员' : '添加管理员'" width="min(480px, 90vw)" :footer="false">
      <t-form :data="form" label-width="80px" @submit="submit">
        <div class="form-grid">
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
        </div>
        <div class="dialog-footer">
          <t-button theme="default" @click="dialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="submitting" shape="round">保存</t-button>
        </div>
      </t-form>
    </t-dialog>

    <!-- 修改密码 dialog -->
    <t-dialog v-model:visible="pwdDialogVisible" header="修改密码" width="min(480px, 90vw)" :footer="false">
      <t-form :data="pwdForm" label-width="80px" @submit="changePassword">
        <div class="form-grid">
          <t-form-item label="原密码" name="oldPassword">
            <t-input v-model="pwdForm.oldPassword" type="password" placeholder="当前密码" />
          </t-form-item>
          <t-form-item label="新密码" name="newPassword">
            <t-input v-model="pwdForm.newPassword" type="password" placeholder="至少6位" />
          </t-form-item>
        </div>
        <div class="dialog-footer">
          <t-button theme="default" @click="pwdDialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="pwdLoading" shape="round">确认修改</t-button>
        </div>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { request, formatTime } from "../utils/api";
import { adminColumns } from "../utils/constants";
import { MessagePlugin, DialogPlugin } from "tdesign-vue-next";

const admins = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const editingId = ref("");
const submitting = ref(false);
const pwdDialogVisible = ref(false);
const pwdLoading = ref(false);
const searchQ = ref("");
const page = ref(1);
const pageSize = ref(20);

const filteredAdmins = computed(() => {
  if (!searchQ.value) return admins.value;
  const q = searchQ.value.toLowerCase();
  return admins.value.filter(a => a.username.toLowerCase().includes(q) || a.name.toLowerCase().includes(q));
});

const pagedAdmins = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return filteredAdmins.value.slice(start, start + pageSize.value);
});

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

function openPwdDialog() {
  pwdForm.oldPassword = "";
  pwdForm.newPassword = "";
  pwdDialogVisible.value = true;
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
    pwdDialogVisible.value = false;
    MessagePlugin.success("密码已修改");
  } catch (error) {
    MessagePlugin.error(error.message);
  } finally {
    pwdLoading.value = false;
  }
}

onMounted(load);
</script>
