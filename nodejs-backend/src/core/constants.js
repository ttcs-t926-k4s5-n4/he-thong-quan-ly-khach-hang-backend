'use strict';
/** Hằng số nghiệp vụ dùng chung cho epic SCRUM-19 (Lead & Marketing). */

const LEAD_STATUSES = ['Mới', 'Đang liên hệ', 'Đủ điều kiện', 'Không đạt', 'Đã chuyển đổi'];
const LEAD_STATUS_NEW = 'Mới';
const LEAD_STATUS_CONVERTED = 'Đã chuyển đổi';
const LEAD_STATUS_DISQUALIFIED = 'Không đạt';

const LEAD_SOURCES = {
  web_form: 'Biểu mẫu website',
  su_kien: 'Sự kiện',
  hoi_thao: 'Hội thảo',
  danh_thiep: 'Danh thiếp',
  gioi_thieu: 'Giới thiệu',
  quang_cao: 'Quảng cáo',
  khac: 'Khác',
};
// "web_form" chỉ do biểu mẫu nhúng sinh ra, không cho nhập tay / nhập Excel
const MANUAL_SOURCES = Object.keys(LEAD_SOURCES).filter((k) => k !== 'web_form');

const CAMPAIGN_CHANNELS = {
  facebook: 'Facebook',
  google_ads: 'Google Ads',
  email: 'Email marketing',
  zalo: 'Zalo',
  website: 'Website / SEO',
  su_kien: 'Sự kiện',
  hoi_thao: 'Hội thảo',
  khac: 'Khác',
};

const OPPORTUNITY_STAGES = ['Mới', 'Đang đàm phán', 'Thắng', 'Thua'];
const STAGE_WON = 'Thắng';
const STAGE_LOST = 'Thua';
const OPEN_STAGES = ['Mới', 'Đang đàm phán'];

module.exports = {
  LEAD_STATUSES, LEAD_STATUS_NEW, LEAD_STATUS_CONVERTED, LEAD_STATUS_DISQUALIFIED,
  LEAD_SOURCES, MANUAL_SOURCES, CAMPAIGN_CHANNELS,
  OPPORTUNITY_STAGES, STAGE_WON, STAGE_LOST, OPEN_STAGES,
};
