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

package org.apache.dolphinscheduler.api.audit;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class OperatorUtilsTest {

    @Test
    void getParamsMap_returnsEmptyMap_whenParameterNamesIsNull() {
        JoinPoint joinPoint = mock(JoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);

        when(joinPoint.getArgs()).thenReturn(new Object[]{"arg0"});
        when(signature.getParameterNames()).thenReturn(null);

        Map<String, Object> result = OperatorUtils.getParamsMap(joinPoint, signature);

        assertTrue(result.isEmpty(),
                "Expected empty map when getParameterNames() returns null (Spring 6 guard)");
    }

    @Test
    void getParamsMap_returnsPopulatedMap_whenParameterNamesIsNonNull() {
        JoinPoint joinPoint = mock(JoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);

        when(joinPoint.getArgs()).thenReturn(new Object[]{"value1", 42});
        when(signature.getParameterNames()).thenReturn(new String[]{"param1", "param2"});

        Map<String, Object> result = OperatorUtils.getParamsMap(joinPoint, signature);

        assertEquals(2, result.size());
        assertEquals("value1", result.get("param1"));
        assertEquals(42, result.get("param2"));
    }
}
