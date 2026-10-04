/**
 * 统一的用户提示层：把 ElMessage / ElMessageBox / ElNotification 收成一套语义化 API。
 *
 * 约定：
 *   - 轻量结果（成功 / 失败 / 校验）→ 顶部墨条 toast（notice-ink），深底浅字，
 *     与默认白底 toast 区分，重要操作结果"闪"一下就能看到；
 *   - 需要用户确认的耗时 / 危险操作 → 弹框确认（confirmAction）；
 *   - 关键完成（生成 / 导出）→ 额外弹一条右下角通知，保留更久。
 * 这样全站反馈口径一致，不会出现"有的地方弹提示、有的地方只在控制台报错"。
 */
import { ElMessage, ElMessageBox, ElNotification } from "element-plus";

type NoticeKind = "success" | "error" | "warning" | "info";

/** 顶部墨条提示：深色底 + 快速淡入，成功/失败都能被一眼捕捉。 */
function ink(message: string, kind: NoticeKind): void {
  ElMessage({
    message,
    type: kind,
    customClass: "notice-ink",
    duration: kind === "error" ? 4200 : 2600,
    showClose: true,
    grouping: true,
  });
}

/** 从任意错误对象里取出可读文案；取不到时用兜底文案。 */
export function messageOf(err: unknown, fallback = "操作失败，请稍后重试。"): string {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === "string" && err.trim()) return err;
  return fallback;
}

export const notice = {
  success: (message: string): void => ink(message, "success"),
  error: (err: unknown, fallback?: string): void => ink(messageOf(err, fallback), "error"),
  warn: (message: string): void => ink(message, "warning"),
  info: (message: string): void => ink(message, "info"),

  /** 关键完成事件：右下角通知，摘要更完整、停留更久。 */
  done: (title: string, message: string): void => {
    ElNotification({
      title,
      message,
      type: "success",
      position: "bottom-right",
      duration: 4200,
      customClass: "notice-ink",
    });
  },
};

/**
 * 需要用户显式确认的耗时 / 危险操作。
 * 用户取消（或关闭弹框）时返回 false，而不是抛异常，方便调用方直接 if 判断。
 */
export async function confirmAction(
  message: string,
  title = "请确认操作",
  confirmText = "继续",
): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: confirmText,
      cancelButtonText: "取消",
      type: "warning",
      customClass: "notice-dialog",
    });
    return true;
  } catch {
    return false;
  }
}
