/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.dolphinscheduler.plugin.datasource.hive;

import static org.apache.dolphinscheduler.plugin.datasource.api.utils.PasswordUtils.encodePassword;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mockStatic;

import org.apache.dolphinscheduler.common.utils.PropertyUtils;
import org.apache.dolphinscheduler.plugin.datasource.hive.param.HiveConnectionParam;
import org.apache.dolphinscheduler.spi.enums.DbType;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.apache.dolphinscheduler.common.constants.Constants.HADOOP_SECURITY_AUTHENTICATION_STARTUP_STATE;
import static org.apache.dolphinscheduler.common.constants.Constants.JAVA_SECURITY_KRB5_CONF_PATH;

@ExtendWith(MockitoExtension.class)
class HivePooledDataSourceClientTest {

    private HiveConnectionParam buildParam() {
        HiveConnectionParam param = new HiveConnectionParam();
        param.setUser("testUser");
        param.setPassword(encodePassword("testPass"));
        param.setAddress("jdbc:hive2://localhost:10000");
        param.setDatabase("default");
        param.setJdbcUrl("jdbc:hive2://localhost:10000/default");
        return param;
    }

    @Test
    void checkKerberosEnv_kerberosDisabled_doesNotCallReflection() {
        try (MockedStatic<PropertyUtils> propUtils = mockStatic(PropertyUtils.class)) {
            propUtils.when(() -> PropertyUtils.getBoolean(eq(HADOOP_SECURITY_AUTHENTICATION_STARTUP_STATE), eq(false)))
                    .thenReturn(false);
            propUtils.when(() -> PropertyUtils.getString(any())).thenReturn(null);

            HivePooledDataSourceClient client = new HivePooledDataSourceClient(buildParam(), DbType.HIVE);
        }
    }

    @Test
    void checkKerberosEnv_kerberosEnabledWithNonExistentKrb5File_throwsRuntimeException() {
        try (MockedStatic<PropertyUtils> propUtils = mockStatic(PropertyUtils.class)) {
            propUtils.when(() -> PropertyUtils.getBoolean(eq(HADOOP_SECURITY_AUTHENTICATION_STARTUP_STATE), eq(false)))
                    .thenReturn(true);
            propUtils.when(() -> PropertyUtils.getString(eq(JAVA_SECURITY_KRB5_CONF_PATH)))
                    .thenReturn("/nonexistent/krb5.conf");
            propUtils.when(() -> PropertyUtils.getString(any())).thenReturn("/nonexistent/krb5.conf");

            assertThrows(RuntimeException.class,
                    () -> new HivePooledDataSourceClient(buildParam(), DbType.HIVE),
                    "Expected RuntimeException when Kerberos is enabled but krb5.conf does not exist");
        }
    }
}
