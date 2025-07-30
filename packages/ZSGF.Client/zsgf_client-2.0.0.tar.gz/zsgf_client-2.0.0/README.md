# ZSGF.Client

![PyPI - Version](https://img.shields.io/pypi/v/ZSGF.Client)

## 要求

Python 3.8+

## 安装与使用

```sh
pip install ZSGF.Client
```

然后导入该包

```python
import ZSGF.Client
```

## 入门指南

```python

import ZSGF.Client
from ZSGF.Client.rest import ApiException
from pprint import pprint

# 定义主机地址
# 有关所有支持的配置参数列表，请参阅 configuration.py 文件。

configuration = ZSGF.Client.Configuration(
    host = "https://apiserver.com"
)

# 客户端必须根据 API 服务器的安全策略配置身份验证和授权参数。
# 下面为每种认证方法都提供了示例，请使用能满足您认证需求的示例。
# 配置 Bearer 认证：Bearer

configuration = ZSGF.Client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)


# 使用 API 客户端的实例进入一个上下文环境
with ZSGF.Client.ApiClient(configuration) as api_client:
    # 创建 API 类的一个实例
    api_instance = ZSGF.Client.AccessTokenApi(api_client)
    id = 56 # int | 
    app_key = 'app_key_example' # str | 

    try:
        # 删除令牌
        api_response = api_instance.access_token_delete(id, app_key)
        print("The response of AccessTokenApi->access_token_delete:\n")
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling AccessTokenApi->access_token_delete: %s\n" % e)

```

## API 文档说明

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*AccessTokenApi* | [**access_token_delete**](docs/AccessTokenApi.md#access_token_delete) | **DELETE** /AccessToken/{appKey}/{id} | 删除令牌
*AccessTokenApi* | [**access_token_post**](docs/AccessTokenApi.md#access_token_post) | **POST** /AccessToken/{appKey} | 创建令牌
*AccessTokenApi* | [**access_token_put**](docs/AccessTokenApi.md#access_token_put) | **PUT** /AccessToken/{appKey}/{id} | 更新令牌
*AccessTokenApi* | [**access_tokens**](docs/AccessTokenApi.md#access_tokens) | **GET** /AccessToken/{appKey} | 令牌列表
*AlipayApi* | [**alipay_create_order**](docs/AlipayApi.md#alipay_create_order) | **POST** /Alipay/{appKey}/CreateOrder | 创建订单 - 当面付
*AlipayApi* | [**alipay_create_order_page_pay**](docs/AlipayApi.md#alipay_create_order_page_pay) | **POST** /Alipay/{appKey}/CreateOrderPagePay | 创建订单 - PC支付
*AlipayApi* | [**alipay_create_order_wap_pay**](docs/AlipayApi.md#alipay_create_order_wap_pay) | **POST** /Alipay/{appKey}/CreateOrderWapPay | 创建订单 - WAP支付
*AlipayApi* | [**alipay_order_detail**](docs/AlipayApi.md#alipay_order_detail) | **GET** /Alipay/{appKey}/OrderDetail | 订单详情
*AlipayApi* | [**alipay_order_refund**](docs/AlipayApi.md#alipay_order_refund) | **POST** /Alipay/{appKey}/OrderRefund | 订单退款
*AlipayApi* | [**alipay_return_page_notify**](docs/AlipayApi.md#alipay_return_page_notify) | **POST** /Alipay/{appKey}/ReturnPageNotify | 支付成功同步通知
*AppApi* | [**app**](docs/AppApi.md#app) | **GET** /App/{appKey} | 应用详情
*AppApi* | [**app2_fa**](docs/AppApi.md#app2_fa) | **GET** /App/{appKey}/2FA | 双因素验证 获取
*AppApi* | [**app2_fa_check**](docs/AppApi.md#app2_fa_check) | **GET** /App/{appKey}/2FACheck | 双因素验证 验证
*AppApi* | [**app_check_version**](docs/AppApi.md#app_check_version) | **GET** /App/{appKey}/CheckVersion | 更新应用数据库
*AppApi* | [**app_delete**](docs/AppApi.md#app_delete) | **DELETE** /App/{appKey} | 删除应用
*AppApi* | [**app_info**](docs/AppApi.md#app_info) | **GET** /App/{appKey}/Info | 应用详情
*AppApi* | [**app_post**](docs/AppApi.md#app_post) | **POST** /App | 创建应用
*AppApi* | [**app_put**](docs/AppApi.md#app_put) | **PUT** /App/{appKey} | 更新应用
*AppApi* | [**app_transfer**](docs/AppApi.md#app_transfer) | **GET** /App/{appKey}/Transfer | 转移应用
*AppApi* | [**apps**](docs/AppApi.md#apps) | **GET** /App | 应用列表
*AppSettingApi* | [**app_service_setting_group**](docs/AppSettingApi.md#app_service_setting_group) | **GET** /AppSetting/{appKey}/Groups/{id} | 获取服务分组详情
*AppSettingApi* | [**app_service_setting_group_delete**](docs/AppSettingApi.md#app_service_setting_group_delete) | **DELETE** /AppSetting/{appKey}/Groups/{id} | 删除服务分组
*AppSettingApi* | [**app_service_setting_group_post**](docs/AppSettingApi.md#app_service_setting_group_post) | **POST** /AppSetting/{appKey}/Groups | 添加服务分组
*AppSettingApi* | [**app_service_setting_group_put**](docs/AppSettingApi.md#app_service_setting_group_put) | **PUT** /AppSetting/{appKey}/Groups/{id} | 更新服务分组
*AppSettingApi* | [**app_service_setting_groups**](docs/AppSettingApi.md#app_service_setting_groups) | **GET** /AppSetting/{appKey}/Groups | 获取服务分组列表
*AppSettingApi* | [**app_service_setting_item**](docs/AppSettingApi.md#app_service_setting_item) | **GET** /AppSetting/{appKey}/Items/{id} | 服务配置项详情
*AppSettingApi* | [**app_service_setting_item_delete**](docs/AppSettingApi.md#app_service_setting_item_delete) | **DELETE** /AppSetting/{appKey}/Items/{id} | 删除服务配置项
*AppSettingApi* | [**app_service_setting_item_post**](docs/AppSettingApi.md#app_service_setting_item_post) | **POST** /AppSetting/{appKey}/Items | 添加服务配置项
*AppSettingApi* | [**app_service_setting_item_put**](docs/AppSettingApi.md#app_service_setting_item_put) | **PUT** /AppSetting/{appKey}/Items/{id} | 更新服务配置项
*AppSettingApi* | [**app_service_setting_items**](docs/AppSettingApi.md#app_service_setting_items) | **GET** /AppSetting/{appKey}/Items | 服务配置项列表
*AppSettingApi* | [**app_service_setting_provider**](docs/AppSettingApi.md#app_service_setting_provider) | **GET** /AppSetting/{appKey}/Providers/{id} | 获取服务商详情
*AppSettingApi* | [**app_service_setting_provider_delete**](docs/AppSettingApi.md#app_service_setting_provider_delete) | **DELETE** /AppSetting/{appKey}/Providers/{id} | 删除服务商
*AppSettingApi* | [**app_service_setting_provider_post**](docs/AppSettingApi.md#app_service_setting_provider_post) | **POST** /AppSetting/{appKey}/Providers | 添加服务商
*AppSettingApi* | [**app_service_setting_provider_put**](docs/AppSettingApi.md#app_service_setting_provider_put) | **PUT** /AppSetting/{appKey}/Providers/{id} | 更新服务商
*AppSettingApi* | [**app_service_setting_providers**](docs/AppSettingApi.md#app_service_setting_providers) | **GET** /AppSetting/{appKey}/Providers | 获取服务商列表
*AppSettingApi* | [**app_setting**](docs/AppSettingApi.md#app_setting) | **GET** /AppSetting/{appKey}/{id} | 配置详情
*AppSettingApi* | [**app_setting_delete**](docs/AppSettingApi.md#app_setting_delete) | **DELETE** /AppSetting/{appKey}/{id} | 删除配置
*AppSettingApi* | [**app_setting_post**](docs/AppSettingApi.md#app_setting_post) | **POST** /AppSetting/{appKey} | 增加配置
*AppSettingApi* | [**app_setting_put**](docs/AppSettingApi.md#app_setting_put) | **PUT** /AppSetting/{appKey}/{id} | 更新配置
*AppSettingApi* | [**app_settings**](docs/AppSettingApi.md#app_settings) | **GET** /AppSetting/{appKey} | 配置列表
*AuthorizePolicyApi* | [**authorize_policies**](docs/AuthorizePolicyApi.md#authorize_policies) | **GET** /AuthorizePolicy/{appKey} | 获取鉴权策略列表
*AuthorizePolicyApi* | [**authorize_policy**](docs/AuthorizePolicyApi.md#authorize_policy) | **GET** /AuthorizePolicy/{appKey}/{id} | 获取鉴权策略详情
*AuthorizePolicyApi* | [**authorize_policy_delete**](docs/AuthorizePolicyApi.md#authorize_policy_delete) | **DELETE** /AuthorizePolicy/{appKey}/{id} | 删除鉴权策略
*AuthorizePolicyApi* | [**authorize_policy_post**](docs/AuthorizePolicyApi.md#authorize_policy_post) | **POST** /AuthorizePolicy/{appKey} | 添加鉴权策略
*AuthorizePolicyApi* | [**authorize_policy_put**](docs/AuthorizePolicyApi.md#authorize_policy_put) | **PUT** /AuthorizePolicy/{appKey}/{id} | 更新鉴权策略
*CurrencyApi* | [**currencies**](docs/CurrencyApi.md#currencies) | **GET** /Currency/{appKey} | 获取货币列表
*CurrencyApi* | [**currency**](docs/CurrencyApi.md#currency) | **GET** /Currency/{appKey}/{id} | 获取货币详情
*CurrencyApi* | [**currency_delete**](docs/CurrencyApi.md#currency_delete) | **DELETE** /Currency/{appKey}/{id} | 删除货币
*CurrencyApi* | [**currency_exchange_rate_delete**](docs/CurrencyApi.md#currency_exchange_rate_delete) | **DELETE** /Currency/{appKey}/ExchangeRates/{id} | 删除汇率
*CurrencyApi* | [**currency_exchange_rate_put**](docs/CurrencyApi.md#currency_exchange_rate_put) | **PUT** /Currency/{appKey}/ExchangeRates/{code} | 更新汇率
*CurrencyApi* | [**currency_exchange_rates**](docs/CurrencyApi.md#currency_exchange_rates) | **GET** /Currency/{appKey}/ExchangeRates/{code} | 获取汇率列表
*CurrencyApi* | [**currency_post**](docs/CurrencyApi.md#currency_post) | **POST** /Currency/{appKey} | 创建新货币
*CurrencyApi* | [**currency_put**](docs/CurrencyApi.md#currency_put) | **PUT** /Currency/{appKey}/{id} | 更新货币信息
*CurrencyApi* | [**currency_transactions**](docs/CurrencyApi.md#currency_transactions) | **GET** /Currency/{appKey}/Transactions | 获取货币交易记录
*DingTalkApi* | [**ding_talk_user_info**](docs/DingTalkApi.md#ding_talk_user_info) | **GET** /DingTalk/{appKey}/UserInfo | 获取用户资料
*FileApi* | [**file_create_folder**](docs/FileApi.md#file_create_folder) | **POST** /File/{appKey}/CreateFolder | 创建文件夹
*FileApi* | [**file_delete**](docs/FileApi.md#file_delete) | **DELETE** /File/{appKey} | 删除文件或文件夹
*FileApi* | [**file_rename**](docs/FileApi.md#file_rename) | **POST** /File/{appKey}/Rename | 重命名文件或文件夹
*FileApi* | [**file_upload**](docs/FileApi.md#file_upload) | **POST** /File/{appKey}/Upload | 上传文件
*FileApi* | [**files**](docs/FileApi.md#files) | **GET** /File/{appKey} | 获取文件列表
*OAuthApi* | [**o_auth_authorize**](docs/OAuthApi.md#o_auth_authorize) | **POST** /OAuth/{appKey}/Authorize | 获取access_token
*OAuthApi* | [**o_auth_consents**](docs/OAuthApi.md#o_auth_consents) | **GET** /OAuth/{appKey}/Consents | 授权记录
*OAuthApi* | [**o_auth_delete_consent**](docs/OAuthApi.md#o_auth_delete_consent) | **DELETE** /OAuth/{appKey}/Consents/{id} | 删除授权记录
*OAuthApi* | [**o_auth_grant_code**](docs/OAuthApi.md#o_auth_grant_code) | **POST** /OAuth/{appKey}/GrantCode | 申请授权码
*OAuthApi* | [**o_auth_profile**](docs/OAuthApi.md#o_auth_profile) | **GET** /OAuth/{appKey}/Profile | 获取个人资料
*OrderApi* | [**order**](docs/OrderApi.md#order) | **GET** /Order/{appKey}/{id} | 获取订单详情
*OrderApi* | [**order_create**](docs/OrderApi.md#order_create) | **POST** /Order/{appKey}/Create | 创建订单
*OrderApi* | [**orders**](docs/OrderApi.md#orders) | **GET** /Order/{appKey} | 获取订单列表
*ProjectApi* | [**project**](docs/ProjectApi.md#project) | **GET** /Project/{id} | 项目详情
*ProjectApi* | [**project_delete**](docs/ProjectApi.md#project_delete) | **DELETE** /Project/{id} | 删除项目
*ProjectApi* | [**project_post**](docs/ProjectApi.md#project_post) | **POST** /Project | 创建项目
*ProjectApi* | [**project_put**](docs/ProjectApi.md#project_put) | **PUT** /Project/{id} | 更新项目
*ProjectApi* | [**projects**](docs/ProjectApi.md#projects) | **GET** /Project | 项目列表
*ServiceSettingApi* | [**service_setting**](docs/ServiceSettingApi.md#service_setting) | **GET** /ServiceSetting/{id} | 获取配置详情
*ServiceSettingApi* | [**service_setting_delete**](docs/ServiceSettingApi.md#service_setting_delete) | **DELETE** /ServiceSetting/{id} | 删除配置
*ServiceSettingApi* | [**service_setting_group**](docs/ServiceSettingApi.md#service_setting_group) | **GET** /ServiceSetting/Groups/{id} | 获取服务分组详情
*ServiceSettingApi* | [**service_setting_group_delete**](docs/ServiceSettingApi.md#service_setting_group_delete) | **DELETE** /ServiceSetting/Groups/{id} | 删除服务分组
*ServiceSettingApi* | [**service_setting_group_post**](docs/ServiceSettingApi.md#service_setting_group_post) | **POST** /ServiceSetting/Groups | 添加服务分组
*ServiceSettingApi* | [**service_setting_group_put**](docs/ServiceSettingApi.md#service_setting_group_put) | **PUT** /ServiceSetting/Groups/{id} | 更新服务分组
*ServiceSettingApi* | [**service_setting_groups**](docs/ServiceSettingApi.md#service_setting_groups) | **GET** /ServiceSetting/Groups | 获取服务分组列表
*ServiceSettingApi* | [**service_setting_item**](docs/ServiceSettingApi.md#service_setting_item) | **GET** /ServiceSetting/Items/{id} | 服务配置详情
*ServiceSettingApi* | [**service_setting_item_delete**](docs/ServiceSettingApi.md#service_setting_item_delete) | **DELETE** /ServiceSetting/Items/{id} | 删除服务配置
*ServiceSettingApi* | [**service_setting_item_post**](docs/ServiceSettingApi.md#service_setting_item_post) | **POST** /ServiceSetting/Items | 添加服务配置
*ServiceSettingApi* | [**service_setting_item_put**](docs/ServiceSettingApi.md#service_setting_item_put) | **PUT** /ServiceSetting/Items/{id} | 更新服务配置
*ServiceSettingApi* | [**service_setting_items**](docs/ServiceSettingApi.md#service_setting_items) | **GET** /ServiceSetting/Items | 服务配置列表
*ServiceSettingApi* | [**service_setting_post**](docs/ServiceSettingApi.md#service_setting_post) | **POST** /ServiceSetting | 增加配置
*ServiceSettingApi* | [**service_setting_provider**](docs/ServiceSettingApi.md#service_setting_provider) | **GET** /ServiceSetting/Providers/{id} | 获取服务商详情
*ServiceSettingApi* | [**service_setting_provider_delete**](docs/ServiceSettingApi.md#service_setting_provider_delete) | **DELETE** /ServiceSetting/Providers/{id} | 删除服务商
*ServiceSettingApi* | [**service_setting_provider_post**](docs/ServiceSettingApi.md#service_setting_provider_post) | **POST** /ServiceSetting/Providers | 添加服务商
*ServiceSettingApi* | [**service_setting_provider_put**](docs/ServiceSettingApi.md#service_setting_provider_put) | **PUT** /ServiceSetting/Providers/{id} | 更新服务商
*ServiceSettingApi* | [**service_setting_providers**](docs/ServiceSettingApi.md#service_setting_providers) | **GET** /ServiceSetting/Providers | 获取服务商列表
*ServiceSettingApi* | [**service_setting_put**](docs/ServiceSettingApi.md#service_setting_put) | **PUT** /ServiceSetting/{id} | 更新配置
*ServiceSettingApi* | [**service_settings**](docs/ServiceSettingApi.md#service_settings) | **GET** /ServiceSetting | 获取配置列表
*StorageApi* | [**storage_aggregate**](docs/StorageApi.md#storage_aggregate) | **GET** /Storage/{appKey}/{table}/Aggregate | 聚合查询
*StorageApi* | [**storage_clear**](docs/StorageApi.md#storage_clear) | **DELETE** /Storage/{appKey}/{table}/Clear | 清空表数据
*StorageApi* | [**storage_delete**](docs/StorageApi.md#storage_delete) | **DELETE** /Storage/{appKey}/{table}/{id} | 删除数据
*StorageApi* | [**storage_delete_index**](docs/StorageApi.md#storage_delete_index) | **DELETE** /Storage/{appKey}/{table}/indexes | 删除索引
*StorageApi* | [**storage_detail**](docs/StorageApi.md#storage_detail) | **GET** /Storage/{appKey}/{table}/{id} | 数据详情
*StorageApi* | [**storage_execute_function**](docs/StorageApi.md#storage_execute_function) | **GET** /Storage/{appKey}/ExecuteFunction | 执行函数
*StorageApi* | [**storage_export**](docs/StorageApi.md#storage_export) | **GET** /Storage/{appKey}/{table}/Export | 导出数据
*StorageApi* | [**storage_import**](docs/StorageApi.md#storage_import) | **POST** /Storage/{appKey}/{table}/Import | 导入数据
*StorageApi* | [**storage_indexes**](docs/StorageApi.md#storage_indexes) | **GET** /Storage/{appKey}/{table}/Indexes | 获取索引
*StorageApi* | [**storage_list**](docs/StorageApi.md#storage_list) | **GET** /Storage/{appKey}/{table} | 查询数据
*StorageApi* | [**storage_post**](docs/StorageApi.md#storage_post) | **POST** /Storage/{appKey}/{table} | 添加数据
*StorageApi* | [**storage_post_index**](docs/StorageApi.md#storage_post_index) | **POST** /Storage/{appKey}/{table}/indexes | 添加索引
*StorageApi* | [**storage_put**](docs/StorageApi.md#storage_put) | **PUT** /Storage/{appKey}/{table}/{id} | 更新数据
*StorageApi* | [**storage_remove**](docs/StorageApi.md#storage_remove) | **DELETE** /Storage/{appKey}/{table}/Remove | 删除表
*StorageApi* | [**storage_stats**](docs/StorageApi.md#storage_stats) | **GET** /Storage/{appKey}/{table}/Stats | 数据表统计
*StorageApi* | [**storage_tables**](docs/StorageApi.md#storage_tables) | **GET** /Storage/{appKey}/Tables | 获取数据表
*SystemFileApi* | [**system_file_create_folder**](docs/SystemFileApi.md#system_file_create_folder) | **POST** /SystemFile/CreateFolder | 创建文件夹
*SystemFileApi* | [**system_file_delete**](docs/SystemFileApi.md#system_file_delete) | **DELETE** /SystemFile | 删除文件
*SystemFileApi* | [**system_file_rename**](docs/SystemFileApi.md#system_file_rename) | **POST** /SystemFile/Rename | 重命名文件
*SystemFileApi* | [**system_file_upload**](docs/SystemFileApi.md#system_file_upload) | **POST** /SystemFile | 上传文件
*SystemFileApi* | [**system_files**](docs/SystemFileApi.md#system_files) | **GET** /SystemFile | 获取文件列表
*TeamApi* | [**team_delete**](docs/TeamApi.md#team_delete) | **DELETE** /Team/{id} | 删除团队
*TeamApi* | [**team_post**](docs/TeamApi.md#team_post) | **POST** /Team | 创建团队
*TeamApi* | [**team_put**](docs/TeamApi.md#team_put) | **PUT** /Team/{id} | 更新团队信息
*TeamApi* | [**teams**](docs/TeamApi.md#teams) | **GET** /Team | 获取团队列表
*UserApi* | [**user**](docs/UserApi.md#user) | **GET** /User/{appKey}/{id} | 获取用户详情
*UserApi* | [**user_clear**](docs/UserApi.md#user_clear) | **DELETE** /User/{appKey}/Clear | 清空用户数据
*UserApi* | [**user_common_interests**](docs/UserApi.md#user_common_interests) | **GET** /User/{appKey}/Friends/CommonInterests | 有共同爱好的用户推荐
*UserApi* | [**user_delete**](docs/UserApi.md#user_delete) | **DELETE** /User/{appKey}/{id} | 删除用户
*UserApi* | [**user_email_sign_in**](docs/UserApi.md#user_email_sign_in) | **POST** /User/{appKey}/EmailSignIn | 邮箱登录
*UserApi* | [**user_email_sign_up**](docs/UserApi.md#user_email_sign_up) | **POST** /User/{appKey}/EmailSignUp | 邮箱注册
*UserApi* | [**user_export**](docs/UserApi.md#user_export) | **GET** /User/{appKey}/Export | 导出用户数据
*UserApi* | [**user_follow_user**](docs/UserApi.md#user_follow_user) | **POST** /User/{appKey}/Follower/{userId} | 关注用户
*UserApi* | [**user_follower_put**](docs/UserApi.md#user_follower_put) | **PUT** /User/{appKey}/Follower/{id} | 更新粉丝
*UserApi* | [**user_followers**](docs/UserApi.md#user_followers) | **GET** /User/{appKey}/Followers | 获取我的粉丝列表
*UserApi* | [**user_following**](docs/UserApi.md#user_following) | **GET** /User/{appKey}/Following | 获取我的关注列表
*UserApi* | [**user_friends_near_by**](docs/UserApi.md#user_friends_near_by) | **GET** /User/{appKey}/Friends/NearBy | 附近的用户推荐
*UserApi* | [**user_import**](docs/UserApi.md#user_import) | **POST** /User/{appKey}/Import | 导入用户数据
*UserApi* | [**user_location**](docs/UserApi.md#user_location) | **GET** /User/{appKey}/Location/{id} | 获取位置详情
*UserApi* | [**user_location_delete**](docs/UserApi.md#user_location_delete) | **DELETE** /User/{appKey}/Location/{id} | 删除位置
*UserApi* | [**user_location_post**](docs/UserApi.md#user_location_post) | **POST** /User/{appKey}/Location | 添加位置
*UserApi* | [**user_location_put**](docs/UserApi.md#user_location_put) | **PUT** /User/{appKey}/Location/{id} | 更新位置
*UserApi* | [**user_locations**](docs/UserApi.md#user_locations) | **GET** /User/{appKey}/Locations | 获取位置列表
*UserApi* | [**user_mutual_followers**](docs/UserApi.md#user_mutual_followers) | **GET** /User/{appKey}/Friends/MutualFollowers | 有共同粉丝的用户推荐
*UserApi* | [**user_mutual_followings**](docs/UserApi.md#user_mutual_followings) | **GET** /User/{appKey}/Friends/MutualFollowings | 有共同关注的用户推荐
*UserApi* | [**user_o_auth_account_bind**](docs/UserApi.md#user_o_auth_account_bind) | **POST** /User/{appKey}/OAuthAccountBind | 外部账号 绑定
*UserApi* | [**user_o_auth_account_sign_in**](docs/UserApi.md#user_o_auth_account_sign_in) | **POST** /User/{appKey}/OAuthAccountSignIn | 外部账号 登录
*UserApi* | [**user_o_auth_accounts**](docs/UserApi.md#user_o_auth_accounts) | **GET** /User/{appKey}/OAuthAccounts | 外部账号 绑定列表
*UserApi* | [**user_o_auth_accounts_put_bind**](docs/UserApi.md#user_o_auth_accounts_put_bind) | **PUT** /User/{appKey}/OAuthAccounts/{id} | 外部账号 更新绑定
*UserApi* | [**user_o_auth_accounts_un_bind**](docs/UserApi.md#user_o_auth_accounts_un_bind) | **DELETE** /User/{appKey}/OAuthAccounts/{id} | 外部账号 删除绑定
*UserApi* | [**user_phone_sign_in**](docs/UserApi.md#user_phone_sign_in) | **POST** /User/{appKey}/PhoneSignIn | 手机登录
*UserApi* | [**user_phone_sign_up**](docs/UserApi.md#user_phone_sign_up) | **POST** /User/{appKey}/PhoneSignUp | 手机注册
*UserApi* | [**user_profile**](docs/UserApi.md#user_profile) | **GET** /User/{appKey}/Profile | 获取个人资料
*UserApi* | [**user_put**](docs/UserApi.md#user_put) | **PUT** /User/{appKey}/{id} | 更新用户信息
*UserApi* | [**user_qr_code_pre_sign_in**](docs/UserApi.md#user_qr_code_pre_sign_in) | **POST** /User/{appKey}/QRCodePreSignIn | 微信小程序 - 预登陆
*UserApi* | [**user_qr_code_scan**](docs/UserApi.md#user_qr_code_scan) | **POST** /User/{appKey}/QRCodeScan | 微信小程序 - 扫码
*UserApi* | [**user_qr_code_sign_in**](docs/UserApi.md#user_qr_code_sign_in) | **POST** /User/{appKey}/QRCodeSignIn | 微信小程序 - 网页登录
*UserApi* | [**user_qr_code_sign_up**](docs/UserApi.md#user_qr_code_sign_up) | **POST** /User/{appKey}/QRCodeSignUp | 微信小程序 - 注册
*UserApi* | [**user_reset_pwd**](docs/UserApi.md#user_reset_pwd) | **POST** /User/{appKey}/ResetPwd | 重置密码
*UserApi* | [**user_send_email_code**](docs/UserApi.md#user_send_email_code) | **POST** /User/{appKey}/SendEmailCode | 发送邮箱验证码
*UserApi* | [**user_send_sms_code**](docs/UserApi.md#user_send_sms_code) | **POST** /User/{appKey}/SendSMSCode | 发送手机验证码
*UserApi* | [**user_sign_in**](docs/UserApi.md#user_sign_in) | **POST** /User/{appKey}/SignIn | 账号密码 登录
*UserApi* | [**user_sign_up**](docs/UserApi.md#user_sign_up) | **POST** /User/{appKey}/SignUp | 账号密码 注册
*UserApi* | [**user_two_factor_auth**](docs/UserApi.md#user_two_factor_auth) | **GET** /User/{appKey}/TwoFactorAuth | 双因素验证
*UserApi* | [**user_unfollow_user**](docs/UserApi.md#user_unfollow_user) | **DELETE** /User/{appKey}/Follower/{userId} | 取消关注
*UserApi* | [**user_union_id_sign_in**](docs/UserApi.md#user_union_id_sign_in) | **POST** /User/{appKey}/UnionIDSignIn | UnionID登录
*UserApi* | [**user_union_id_sign_up**](docs/UserApi.md#user_union_id_sign_up) | **POST** /User/{appKey}/UnionIDSignUp | UnionID注册
*UserApi* | [**user_update_profile**](docs/UserApi.md#user_update_profile) | **PUT** /User/{appKey}/Profile | 更新个人资料
*UserApi* | [**users**](docs/UserApi.md#users) | **GET** /User/{appKey} | 获取用户列表
*UserCurrencyApi* | [**user_currencies**](docs/UserCurrencyApi.md#user_currencies) | **GET** /UserCurrency/{appKey}/{id} | 获取用户资产
*UserCurrencyApi* | [**user_currency_consume**](docs/UserCurrencyApi.md#user_currency_consume) | **POST** /UserCurrency/{appKey}/CurrencyConsume | 消费虚拟币
*UserCurrencyApi* | [**user_currency_exchange**](docs/UserCurrencyApi.md#user_currency_exchange) | **POST** /UserCurrency/{appKey}/CurrencyExchange | 兑换虚拟币
*UserCurrencyApi* | [**user_currency_recharge**](docs/UserCurrencyApi.md#user_currency_recharge) | **POST** /UserCurrency/{appKey}/CurrencyRecharge | 充值虚拟币
*UserCurrencyApi* | [**user_currency_transactions**](docs/UserCurrencyApi.md#user_currency_transactions) | **GET** /UserCurrency/{appKey}/CurrencyTransactions | 虚拟币交易记录
*UserSettingApi* | [**user_setting**](docs/UserSettingApi.md#user_setting) | **GET** /UserSetting/{appKey}/{id} | 获取用户配置项详情
*UserSettingApi* | [**user_setting_delete**](docs/UserSettingApi.md#user_setting_delete) | **DELETE** /UserSetting/{appKey}/{id} | 删除用户配置项
*UserSettingApi* | [**user_setting_post**](docs/UserSettingApi.md#user_setting_post) | **POST** /UserSetting/{appKey} | 添加用户配置项
*UserSettingApi* | [**user_setting_put**](docs/UserSettingApi.md#user_setting_put) | **PUT** /UserSetting/{appKey}/{id} | 更新用户配置项
*UserSettingApi* | [**user_settings**](docs/UserSettingApi.md#user_settings) | **GET** /UserSetting/{appKey} | 获取用户配置列表
*WechatApi* | [**wechat_decrypt**](docs/WechatApi.md#wechat_decrypt) | **GET** /Wechat/{appKey}/Decrypt | 小程序-解密数据
*WechatApi* | [**wechat_generate_scheme**](docs/WechatApi.md#wechat_generate_scheme) | **POST** /Wechat/{appKey}/GenerateScheme | 小程序-生成scheme码(该接口用于获取小程序 scheme 码，适用于短信、邮件、外部网页、微信内等拉起小程序的业务场景)
*WechatApi* | [**wechat_js_code2_session**](docs/WechatApi.md#wechat_js_code2_session) | **GET** /Wechat/{appKey}/JSCode2Session | 小程序-登录凭证校验
*WechatApi* | [**wechat_js_config**](docs/WechatApi.md#wechat_js_config) | **GET** /Wechat/{appKey}/JSConfig | 公众号H5-JS SDK Config
*WechatApi* | [**wechat_subscribe_msg**](docs/WechatApi.md#wechat_subscribe_msg) | **POST** /Wechat/{appKey}/SubscribeMSG | 公众号H5-发送一次性订阅消息
*WechatApi* | [**wechat_subscribe_send**](docs/WechatApi.md#wechat_subscribe_send) | **POST** /Wechat/{appKey}/SubscribeSend | 小程序-发送订阅消息
*WechatApi* | [**wechat_url_link_generate**](docs/WechatApi.md#wechat_url_link_generate) | **POST** /Wechat/{appKey}/UrlLinkGenerate | 小程序-生成网页跳转地址(获取小程序 URL Link，适用于短信、邮件、网页、微信内等拉起小程序的业务场景)
*WechatApi* | [**wechat_user_info**](docs/WechatApi.md#wechat_user_info) | **GET** /Wechat/{appKey}/UserInfo | 公众号H5-获取用户UnionID
*WechatApi* | [**wechat_wxa_code_get**](docs/WechatApi.md#wechat_wxa_code_get) | **POST** /Wechat/{appKey}/WXACodeGet | 小程序-获取小程序码
*WechatApi* | [**wechat_wxa_code_get_unlimited**](docs/WechatApi.md#wechat_wxa_code_get_unlimited) | **POST** /Wechat/{appKey}/WXACodeGetUnlimited | 小程序-获取小程序码(无限制)


## 数据结构

 - [AccessTokenListResult](docs/AccessTokenListResult.md)
  - [AccessTokenListResultApiResponse](docs/AccessTokenListResultApiResponse.md)
  - [AccessTokenPostRequest](docs/AccessTokenPostRequest.md)
  - [AccessTokenPutRequest](docs/AccessTokenPutRequest.md)
  - [AlipayCreateOrderPagePayRequest](docs/AlipayCreateOrderPagePayRequest.md)
  - [AlipayCreateOrderRequest](docs/AlipayCreateOrderRequest.md)
  - [AlipayCreateOrderWapPayRequest](docs/AlipayCreateOrderWapPayRequest.md)
  - [AlipayTradeQueryResponse](docs/AlipayTradeQueryResponse.md)
  - [AlipayTradeQueryResponseApiResponse](docs/AlipayTradeQueryResponseApiResponse.md)
  - [AlipayTradeRefundResponse](docs/AlipayTradeRefundResponse.md)
  - [AlipayTradeRefundResponseApiResponse](docs/AlipayTradeRefundResponseApiResponse.md)
  - [App](docs/App.md)
  - [AppApiResponse](docs/AppApiResponse.md)
  - [AppCheckVersionResult](docs/AppCheckVersionResult.md)
  - [AppCheckVersionResultApiResponse](docs/AppCheckVersionResultApiResponse.md)
  - [AppInfoItem](docs/AppInfoItem.md)
  - [AppInfoResult](docs/AppInfoResult.md)
  - [AppInfoResultApiResponse](docs/AppInfoResultApiResponse.md)
  - [AppListResult](docs/AppListResult.md)
  - [AppListResultApiResponse](docs/AppListResultApiResponse.md)
  - [AppPostResult](docs/AppPostResult.md)
  - [AppPostResultApiResponse](docs/AppPostResultApiResponse.md)
  - [AppProperty](docs/AppProperty.md)
  - [AppSetting](docs/AppSetting.md)
  - [AppSettingApiResponse](docs/AppSettingApiResponse.md)
  - [AppSettingGroupPostResult](docs/AppSettingGroupPostResult.md)
  - [AppSettingGroupPostResultApiResponse](docs/AppSettingGroupPostResultApiResponse.md)
  - [AppSettingItemPostResult](docs/AppSettingItemPostResult.md)
  - [AppSettingItemPostResultApiResponse](docs/AppSettingItemPostResultApiResponse.md)
  - [AppSettingListApiResponse](docs/AppSettingListApiResponse.md)
  - [AppSettingProviderPostResult](docs/AppSettingProviderPostResult.md)
  - [AppSettingProviderPostResultApiResponse](docs/AppSettingProviderPostResultApiResponse.md)
  - [AppSettingSettingPostResult](docs/AppSettingSettingPostResult.md)
  - [AppSettingSettingPostResultApiResponse](docs/AppSettingSettingPostResultApiResponse.md)
  - [AppUserConsentModel](docs/AppUserConsentModel.md)
  - [AppUserConsentModelListApiResponse](docs/AppUserConsentModelListApiResponse.md)
  - [AppUserListResponse](docs/AppUserListResponse.md)
  - [AppUserResetPwdRequest](docs/AppUserResetPwdRequest.md)
  - [AuthorizePolicy](docs/AuthorizePolicy.md)
  - [AuthorizePolicyApiResponse](docs/AuthorizePolicyApiResponse.md)
  - [AuthorizePolicyListApiResponse](docs/AuthorizePolicyListApiResponse.md)
  - [AuthorizeResult](docs/AuthorizeResult.md)
  - [AuthorizeResultApiResponse](docs/AuthorizeResultApiResponse.md)
  - [BkAgentRespInfo](docs/BkAgentRespInfo.md)
  - [BooleanApiResponse](docs/BooleanApiResponse.md)
  - [ChargeInfo](docs/ChargeInfo.md)
  - [CommonFriendModel](docs/CommonFriendModel.md)
  - [ContributeDetail](docs/ContributeDetail.md)
  - [CreateOrderRequest](docs/CreateOrderRequest.md)
  - [CreateOrderResult](docs/CreateOrderResult.md)
  - [CreateOrderResultApiResponse](docs/CreateOrderResultApiResponse.md)
  - [CreatePostResult](docs/CreatePostResult.md)
  - [CreatePostResultApiResponse](docs/CreatePostResultApiResponse.md)
  - [Currency](docs/Currency.md)
  - [CurrencyApiResponse](docs/CurrencyApiResponse.md)
  - [CurrencyConsumeRequest](docs/CurrencyConsumeRequest.md)
  - [CurrencyExchangeRate](docs/CurrencyExchangeRate.md)
  - [CurrencyExchangeRateApiResponse](docs/CurrencyExchangeRateApiResponse.md)
  - [CurrencyListApiResponse](docs/CurrencyListApiResponse.md)
  - [CurrencyTransaction](docs/CurrencyTransaction.md)
  - [CurrencyTransactionListApiResponse](docs/CurrencyTransactionListApiResponse.md)
  - [DirectoryItem](docs/DirectoryItem.md)
  - [EmailSignInRequest](docs/EmailSignInRequest.md)
  - [EmailSignUpRequest](docs/EmailSignUpRequest.md)
  - [EnterprisePayInfo](docs/EnterprisePayInfo.md)
  - [ExchangeCurrencyRequest](docs/ExchangeCurrencyRequest.md)
  - [ExchangeRatePutRequest](docs/ExchangeRatePutRequest.md)
  - [ExecuteFunctionRequest](docs/ExecuteFunctionRequest.md)
  - [FileItem](docs/FileItem.md)
  - [FileListResult](docs/FileListResult.md)
  - [FileListResultApiResponse](docs/FileListResultApiResponse.md)
  - [FollowerModel](docs/FollowerModel.md)
  - [FollowerPutModel](docs/FollowerPutModel.md)
  - [FulfillmentDetail](docs/FulfillmentDetail.md)
  - [GeoLocationModel](docs/GeoLocationModel.md)
  - [GeoLocationModelApiResponse](docs/GeoLocationModelApiResponse.md)
  - [GeoLocationResponseModel](docs/GeoLocationResponseModel.md)
  - [GoodsDetail](docs/GoodsDetail.md)
  - [GrantRequest](docs/GrantRequest.md)
  - [GrantResult](docs/GrantResult.md)
  - [GrantResultApiResponse](docs/GrantResultApiResponse.md)
  - [HbFqPayInfo](docs/HbFqPayInfo.md)
  - [Int64ApiResponse](docs/Int64ApiResponse.md)
  - [IntactChargeInfo](docs/IntactChargeInfo.md)
  - [ListResponseItem](docs/ListResponseItem.md)
  - [ListResponseItemListApiResponse](docs/ListResponseItemListApiResponse.md)
  - [OAuthAccountBindRequest](docs/OAuthAccountBindRequest.md)
  - [OAuthAccountPutBindRequest](docs/OAuthAccountPutBindRequest.md)
  - [OAuthAccountSignInRequest](docs/OAuthAccountSignInRequest.md)
  - [ObjectApiResponse](docs/ObjectApiResponse.md)
  - [ObjectListApiResponse](docs/ObjectListApiResponse.md)
  - [Order](docs/Order.md)
  - [OrderApiResponse](docs/OrderApiResponse.md)
  - [OrderListResult](docs/OrderListResult.md)
  - [OrderListResultApiResponse](docs/OrderListResultApiResponse.md)
  - [PaymentInfoWithId](docs/PaymentInfoWithId.md)
  - [PhoneSignInRequest](docs/PhoneSignInRequest.md)
  - [PhoneSignUpRequest](docs/PhoneSignUpRequest.md)
  - [PostIndexRequest](docs/PostIndexRequest.md)
  - [PostResult](docs/PostResult.md)
  - [PostResultApiResponse](docs/PostResultApiResponse.md)
  - [PresetPayToolInfo](docs/PresetPayToolInfo.md)
  - [ProfileResult](docs/ProfileResult.md)
  - [ProfileResultApiResponse](docs/ProfileResultApiResponse.md)
  - [Project](docs/Project.md)
  - [ProjectApiResponse](docs/ProjectApiResponse.md)
  - [ProjectListResult](docs/ProjectListResult.md)
  - [ProjectListResultApiResponse](docs/ProjectListResultApiResponse.md)
  - [QRCodePreSignInRequest](docs/QRCodePreSignInRequest.md)
  - [QRCodeScanRequest](docs/QRCodeScanRequest.md)
  - [QRCodeSignInRequest](docs/QRCodeSignInRequest.md)
  - [QRCodeSignUpRequest](docs/QRCodeSignUpRequest.md)
  - [RechargePointRequest](docs/RechargePointRequest.md)
  - [RecommendFriend](docs/RecommendFriend.md)
  - [RefundChargeInfo](docs/RefundChargeInfo.md)
  - [RefundSubFee](docs/RefundSubFee.md)
  - [ReturnPageNotifyRequest](docs/ReturnPageNotifyRequest.md)
  - [SendEmailCodeRequest](docs/SendEmailCodeRequest.md)
  - [SendSMSCodeRequest](docs/SendSMSCodeRequest.md)
  - [ServiceGroup](docs/ServiceGroup.md)
  - [ServiceGroupApiResponse](docs/ServiceGroupApiResponse.md)
  - [ServiceGroupListApiResponse](docs/ServiceGroupListApiResponse.md)
  - [ServiceItem](docs/ServiceItem.md)
  - [ServiceItemApiResponse](docs/ServiceItemApiResponse.md)
  - [ServiceItemListApiResponse](docs/ServiceItemListApiResponse.md)
  - [ServiceProvider](docs/ServiceProvider.md)
  - [ServiceProviderApiResponse](docs/ServiceProviderApiResponse.md)
  - [ServiceProviderListApiResponse](docs/ServiceProviderListApiResponse.md)
  - [ServiceSettingGroupPostResult](docs/ServiceSettingGroupPostResult.md)
  - [ServiceSettingGroupPostResultApiResponse](docs/ServiceSettingGroupPostResultApiResponse.md)
  - [ServiceSettingItemPostResult](docs/ServiceSettingItemPostResult.md)
  - [ServiceSettingItemPostResultApiResponse](docs/ServiceSettingItemPostResultApiResponse.md)
  - [ServiceSettingProviderPostResult](docs/ServiceSettingProviderPostResult.md)
  - [ServiceSettingProviderPostResultApiResponse](docs/ServiceSettingProviderPostResultApiResponse.md)
  - [ServiceSettingSettingPostResult](docs/ServiceSettingSettingPostResult.md)
  - [ServiceSettingSettingPostResultApiResponse](docs/ServiceSettingSettingPostResultApiResponse.md)
  - [Settings](docs/Settings.md)
  - [SettingsApiResponse](docs/SettingsApiResponse.md)
  - [SettingsListApiResponse](docs/SettingsListApiResponse.md)
  - [SetupCode](docs/SetupCode.md)
  - [SetupCodeApiResponse](docs/SetupCodeApiResponse.md)
  - [SignInRequest](docs/SignInRequest.md)
  - [SignUpRequest](docs/SignUpRequest.md)
  - [StorageListResult](docs/StorageListResult.md)
  - [StorageListResultApiResponse](docs/StorageListResultApiResponse.md)
  - [StringApiResponse](docs/StringApiResponse.md)
  - [StringListApiResponse](docs/StringListApiResponse.md)
  - [SubFee](docs/SubFee.md)
  - [SystemDirectoryItem](docs/SystemDirectoryItem.md)
  - [SystemFileItem](docs/SystemFileItem.md)
  - [SystemFileListResult](docs/SystemFileListResult.md)
  - [SystemFileListResultApiResponse](docs/SystemFileListResultApiResponse.md)
  - [TapPayInfo](docs/TapPayInfo.md)
  - [Team](docs/Team.md)
  - [TokenModel](docs/TokenModel.md)
  - [TokenModelApiResponse](docs/TokenModelApiResponse.md)
  - [TradeFundBill](docs/TradeFundBill.md)
  - [TradeSettleDetail](docs/TradeSettleDetail.md)
  - [TradeSettleInfo](docs/TradeSettleInfo.md)
  - [UnionIDSignInRequest](docs/UnionIDSignInRequest.md)
  - [UnionIDSignUpRequest](docs/UnionIDSignUpRequest.md)
  - [UpdateProfileRequest](docs/UpdateProfileRequest.md)
  - [User](docs/User.md)
  - [UserAccessToken](docs/UserAccessToken.md)
  - [UserApiResponse](docs/UserApiResponse.md)
  - [UserCommonInterestsResult](docs/UserCommonInterestsResult.md)
  - [UserCommonInterestsResultApiResponse](docs/UserCommonInterestsResultApiResponse.md)
  - [UserCurrency](docs/UserCurrency.md)
  - [UserCurrencyCurrencyTransResult](docs/UserCurrencyCurrencyTransResult.md)
  - [UserCurrencyCurrencyTransResultApiResponse](docs/UserCurrencyCurrencyTransResultApiResponse.md)
  - [UserCurrencyListApiResponse](docs/UserCurrencyListApiResponse.md)
  - [UserFollowersResult](docs/UserFollowersResult.md)
  - [UserFollowersResultApiResponse](docs/UserFollowersResultApiResponse.md)
  - [UserFollowingResult](docs/UserFollowingResult.md)
  - [UserFollowingResultApiResponse](docs/UserFollowingResultApiResponse.md)
  - [UserFriendsNearByResult](docs/UserFriendsNearByResult.md)
  - [UserFriendsNearByResultApiResponse](docs/UserFriendsNearByResultApiResponse.md)
  - [UserListResult](docs/UserListResult.md)
  - [UserListResultApiResponse](docs/UserListResultApiResponse.md)
  - [UserLocationPostResult](docs/UserLocationPostResult.md)
  - [UserLocationPostResultApiResponse](docs/UserLocationPostResultApiResponse.md)
  - [UserLocationsResult](docs/UserLocationsResult.md)
  - [UserLocationsResultApiResponse](docs/UserLocationsResultApiResponse.md)
  - [UserLogins](docs/UserLogins.md)
  - [UserLoginsListApiResponse](docs/UserLoginsListApiResponse.md)
  - [UserMutualFollowersResult](docs/UserMutualFollowersResult.md)
  - [UserMutualFollowersResultApiResponse](docs/UserMutualFollowersResultApiResponse.md)
  - [UserMutualFollowingsResult](docs/UserMutualFollowingsResult.md)
  - [UserMutualFollowingsResultApiResponse](docs/UserMutualFollowingsResultApiResponse.md)
  - [UserProfileResult](docs/UserProfileResult.md)
  - [UserProfileResultApiResponse](docs/UserProfileResultApiResponse.md)
  - [UserQRCodeScanResult](docs/UserQRCodeScanResult.md)
  - [UserQRCodeScanResultApiResponse](docs/UserQRCodeScanResultApiResponse.md)
  - [UserSetting](docs/UserSetting.md)
  - [UserSettingApiResponse](docs/UserSettingApiResponse.md)
  - [UserSettingListApiResponse](docs/UserSettingListApiResponse.md)
  - [UserSettingPostResult](docs/UserSettingPostResult.md)
  - [UserSettingPostResultApiResponse](docs/UserSettingPostResultApiResponse.md)
  - [VoucherDetail](docs/VoucherDetail.md)
  - [WechatJSConfigResult](docs/WechatJSConfigResult.md)
  - [WechatJSConfigResultApiResponse](docs/WechatJSConfigResultApiResponse.md)