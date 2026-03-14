```
project_root/
├── src/
│   ├── api/
│   │   ├── Request.cpp
│   │   └── Response.cpp
│   ├── auth/
│   │   ├── Authentication.cpp
│   │   └── Authorization.cpp
│   ├── data/
│   │   ├── OrderItemRepository.cpp
│   │   ├── OrderRepository.cpp
│   │   ├── ProductRepository.cpp
│   │   └── UserRepository.cpp
│   ├── main.cpp
│   ├── models/
│   │   ├── Order.cpp
│   │   ├── OrderItem.cpp
│   │   ├── Product.cpp
│   │   └── User.cpp
│   ├── neurax/
│   │   └── NeuraxCore.cpp
│   └── utils/
│       └── ErrorHandler.cpp
├── include/
│   ├── api/
│   │   ├── IHandler.h
│   │   ├── Request.h
│   │   └── Response.h
│   ├── auth/
│   │   ├── Authentication.h
│   │   └── Authorization.h
│   ├── data/
│   │   ├── OrderItemRepository.h
│   │   ├── OrderRepository.h
│   │   ├── ProductRepository.h
│   │   └── UserRepository.h
│   ├── models/
│   │   ├── Order.h
│   │   ├── OrderItem.h
│   │   ├── Product.h
│   │   └── User.h
│   ├── neurax/
│   │   └── NeuraxCore.h
│   └── utils/
│       └── ErrorHandler.h
├── build/
├── config/
├── database/
│   └── schema.sql
├── tests/
├── .gitignore
├── CMakeLists.txt
└── README.md
``````cpp
#ifndef BACKEND_USER_REPOSITORY_H
#define BACKEND_USER_REPOSITORY_H

#include "models/User.h"
#include <string>
#include <optional>
#include <vector>
#include <map>
#include <atomic>

class UserRepository {
public:
    UserRepository() = default;

    std::optional<User> findById(long long id) const;
    std::optional<User> findByUsername(const std::string& username) const;
    std::optional<User> findByEmail(const std::string& email) const;
    User save(User user); // Inserts or updates

private:
    std::map<long long, User> users_;
    std::atomic<long long> nextId_{1}; // Simulate auto-incrementing ID
};

#endif // BACKEND_USER_REPOSITORY_H
``````cpp
#include "data/UserRepository.h"
#include <algorithm>
#include <iostream>

std::optional<User> UserRepository::findById(long long id) const {
    auto it = users_.find(id);
    if (it != users_.end()) {
        return it->second;
    }
    return std::nullopt;
}

std::optional<User> UserRepository::findByUsername(const std::string& username) const {
    for (const auto& pair : users_) {
        if (pair.second.getUsername() == username) {
            return pair.second;
        }
    }
    return std::nullopt;
}

std::optional<User> UserRepository::findByEmail(const std::string& email) const {
    for (const auto& pair : users_) {
        if (pair.second.getEmail() == email) {
            return pair.second;
        }
    }
    return std::nullopt;
}

User UserRepository::save(User user) {
    if (user.getId() == 0) { // New user
        user.setId(nextId_++);
        // Simulate created_at timestamp
        // In a real scenario, this would be handled by the DB or a proper time utility
        user.setCreatedAt(std::string("2023-10-27T10:00:00Z"));
    }
    users_[user.getId()] = user;
    #ifdef DEBUG_NEURAX
    std::cout << "UserRepository: Saved user: " << user.getUsername() << " (ID: " << user.getId() << ")" << std::endl;
    #endif
    return user;
}
``````cpp
#ifndef BACKEND_PRODUCT_REPOSITORY_H
#define BACKEND_PRODUCT_REPOSITORY_H

#include "models/Product.h"
#include <string>
#include <optional>
#include <vector>
#include <map>
#include <atomic>

class ProductRepository {
public:
    ProductRepository() = default;

    std::optional<Product> findById(long long id) const;
    std::vector<Product> findAll() const;
    Product save(Product product); // Inserts or updates
    bool remove(long long id);

private:
    std::map<long long, Product> products_;
    std::atomic<long long> nextId_{1};
};

#endif // BACKEND_PRODUCT_REPOSITORY_H
``````cpp
#include "data/ProductRepository.h"
#include <algorithm>
#include <iostream>

std::optional<Product> ProductRepository::findById(long long id) const {
    auto it = products_.find(id);
    if (it != products_.end()) {
        return it->second;
    }
    return std::nullopt;
}

std::vector<Product> ProductRepository::findAll() const {
    std::vector<Product> allProducts;
    for (const auto& pair : products_) {
        allProducts.push_back(pair.second);
    }
    return allProducts;
}

Product ProductRepository::save(Product product) {
    if (product.getId() == 0) { // New product
        product.setId(nextId_++);
        // Simulate created_at and updated_at timestamps
        product.setCreatedAt("2023-10-27T10:00:00Z"); // Dummy
    }
    product.setUpdatedAt("2023-10-27T10:00:00Z"); // Dummy
    products_[product.getId()] = product;
    #ifdef DEBUG_NEURAX
    std::cout << "ProductRepository: Saved product: " << product.getName() << " (ID: " << product.getId() << ")" << std::endl;
    #endif
    return product;
}

bool ProductRepository::remove(long long id) {
    #ifdef DEBUG_NEURAX
    std::cout << "ProductRepository: Attempting to remove product with ID: " << id << std::endl;
    #endif
    auto it = products_.find(id);
    if (it != products_.end()) {
        products_.erase(it);
        #ifdef DEBUG_NEURAX
        std::cout << "ProductRepository: Successfully removed product with ID: " << id << std::endl;
        #endif
        return true;
    }
    #ifdef DEBUG_NEURAX
    std::cout << "ProductRepository: Product with ID: " << id << " not found for removal." << std::endl;
    #endif
    return false;
}
``````cpp
#ifndef BACKEND_ORDER_REPOSITORY_H
#define BACKEND_ORDER_REPOSITORY_H

#include "models/Order.h"
#include <string>
#include <optional>
#include <vector>
#include <map>
#include <atomic>

class OrderRepository {
public:
    OrderRepository() = default;

    std::optional<Order> findById(long long id) const;
    std::vector<Order> findByUserId(long long userId) const;
    Order save(Order order); // Inserts or updates

private:
    std::map<long long, Order> orders_;
    std::atomic<long long> nextId_{1};
};

#endif // BACKEND_ORDER_REPOSITORY_H
``````cpp
#include "data/OrderRepository.h"
#include <algorithm>
#include <iostream>

std::optional<Order> OrderRepository::findById(long long id) const {
    auto it = orders_.find(id);
    if (it != orders_.end()) {
        return it->second;
    }
    return std::nullopt;
}

std::vector<Order> OrderRepository::findByUserId(long long userId) const {
    std::vector<Order> userOrders;
    for (const auto& pair : orders_) {
        if (pair.second.getUserId() == userId) {
            userOrders.push_back(pair.second);
        }
    }
    return userOrders;
}

Order OrderRepository::save(Order order) {
    if (order.getId() == 0) { // New order
        order.setId(nextId_++);
        // Simulate created_at and updated_at timestamps
        order.setCreatedAt("2023-10-27T10:00:00Z"); // Dummy
        order.setOrderDate("2023-10-27T10:00:00Z"); // Dummy
    }
    order.setUpdatedAt("2023-10-27T10:00:00Z"); // Dummy
    orders_[order.getId()] = order;
    #ifdef DEBUG_NEURAX
    std::cout << "OrderRepository: Saved order (ID: " << order.getId() << ") for User: " << order.getUserId() << std::endl;
    #endif
    return order;
}
``````cpp
#ifndef BACKEND_ORDER_ITEM_REPOSITORY_H
#define BACKEND_ORDER_ITEM_REPOSITORY_H

#include "models/OrderItem.h"
#include <string>
#include <optional>
#include <vector>
#include <map>
#include <atomic>

// For OrderItem, primary key is (order_id, product_id)
// We'll use a nested map or a custom key struct for simplicity in mock
struct OrderItemKey {
    long long orderId;
    long long productId;

    bool operator<(const OrderItemKey& other) const {
        if (orderId != other.orderId) {
            return orderId < other.orderId;
        }
        return productId < other.productId;
    }
};

class OrderItemRepository {
public:
    OrderItemRepository() = default;

    std::vector<OrderItem> findByOrderId(long long orderId) const;
    std::optional<OrderItem> findByOrderAndProductId(long long orderId, long long productId) const;
    OrderItem save(OrderItem item); // Inserts or updates

private:
    std::map<OrderItemKey, OrderItem> orderItems_;
};

#endif // BACKEND_ORDER_ITEM_REPOSITORY_H
``````cpp
#include "data/OrderItemRepository.h"
#include <algorithm>
#include <iostream>

std::vector<OrderItem> OrderItemRepository::findByOrderId(long long orderId) const {
    std::vector<OrderItem> items;
    for (const auto& pair : orderItems_) {
        if (pair.first.orderId == orderId) {
            items.push_back(pair.second);
        }
    }
    return items;
}

std::optional<OrderItem> OrderItemRepository::findByOrderAndProductId(long long orderId, long long productId) const {
    OrderItemKey key = {orderId, productId};
    auto it = orderItems_.find(key);
    if (it != orderItems_.end()) {
        return it->second;
    }
    return std::nullopt;
}

OrderItem OrderItemRepository::save(OrderItem item) {
    OrderItemKey key = {item.getOrderId(), item.getProductId()};
    orderItems_[key] = item;
    #ifdef DEBUG_NEURAX
    std::cout << "OrderItemRepository: Saved order item for Order: " << item.getOrderId() << ", Product: " << item.getProductId() << std::endl;
    #endif
    return item;
}
``````cpp
#ifndef BACKEND_NEURAX_CORE_H
#define BACKEND_NEURAX_CORE_H

#include "auth/Authentication.h"
#include "auth/Authorization.h"
#include "data/UserRepository.h"
#include "data/ProductRepository.h"
#include "data/OrderRepository.h"
#include "data/OrderItemRepository.h"
#include "models/User.h"
#include "models/Product.h"
#include "models/Order.h"
#include "models/OrderItem.h"

#include <string>
#include <optional>
#include <vector>
#include <map>
#include <stdexcept>

// Custom exceptions for business logic errors
class NeuraxException : public std::runtime_error {
public:
    explicit NeuraxException(const std::string& message) : std::runtime_error(message) {}
};

class UserExistsException : public NeuraxException {
public:
    explicit UserExistsException(const std::string& message) : NeuraxException(message) {}
};

class AuthenticationException : public NeuraxException {
public:
    explicit AuthenticationException(const std::string& message) : NeuraxException(message) {}
};

class NotFoundException : public NeuraxException {
public:
    explicit NotFoundException(const std::string& message) : NeuraxException(message) {}
};

class PermissionDeniedException : public NeuraxException {
public:
    explicit PermissionDeniedException(const std::string& message) : NeuraxException(message) {}
};

class InvalidInputException : public NeuraxException {
public:
    explicit InvalidInputException(const std::string& message) : NeuraxException(message) {}
};

class OutOfStockException : public NeuraxException {
public:
    explicit OutOfStockException(const std::string& message) : NeuraxException(message) {}
};


class NeuraxCore {
public:
    // Dependency Injection for repositories (or use singletons for simplicity in demo)
    NeuraxCore(UserRepository& userRepository, ProductRepository& productRepository,
               OrderRepository& orderRepository, OrderItemRepository& orderItemRepository);

    // User Management
    User registerUser(const std::string& username, const std::string& email, const std::string& password);
    std::string loginUser(const std::string& email, const std::string& password);
    std::optional<User> getUserById(long long userId); // For internal use or admin

    // Product Management
    std::vector<Product> getAllProducts();
    std::optional<Product> getProductById(long long productId);
    Product createProduct(long long actingUserId, const std::string& name, const std::string& description,
                          double price, int stockQuantity);
    Product updateProduct(long long actingUserId, long long productId, const std::string& name,
                          const std::string& description, double price, int stockQuantity);
    void deleteProduct(long long actingUserId, long long productId);

    // Order Management
    Order placeOrder(long long userId, const std::map<long long, int>& productQuantities);
    std::vector<Order> getUserOrders(long long userId);
    std::optional<Order> getOrderById(long long actingUserId, long long orderId); // Check ownership or admin
    std::vector<OrderItem> getOrderItems(long long orderId);

private:
    UserRepository& userRepository_;
    ProductRepository& productRepository_;
    OrderRepository& orderRepository_;
    OrderItemRepository& orderItemRepository_;
};

#endif // BACKEND_NEURAX_CORE_H
``````cpp
#include "neurax/NeuraxCore.h"
#include <iostream>
#include <iomanip> // For std::setprecision

#ifdef DEBUG_NEURAX
#define NEURAX_LOG(msg) std::cout << "[NeuraxCore DEBUG] " << msg << std::endl;
#else
#define NEURAX_LOG(msg)
#endif

NeuraxCore::NeuraxCore(UserRepository& userRepository, ProductRepository& productRepository,
                       OrderRepository& orderRepository, OrderItemRepository& orderItemRepository)
    : userRepository_(userRepository),
      productRepository_(productRepository),
      orderRepository_(orderRepository),
      orderItemRepository_(orderItemRepository) {}

// --- User Management ---
User NeuraxCore::registerUser(const std::string& username, const std::string& email, const std::string& password) {
    NEURAX_LOG("Attempting to register user: " << username << ", " << email);

    if (username.empty() || email.empty() || password.empty()) {
        throw InvalidInputException("Username, email, and password cannot be empty.");
    }

    if (userRepository_.findByUsername(username).has_value()) {
        throw UserExistsException("User with this username already exists.");
    }
    if (userRepository_.findByEmail(email).has_value()) {
        throw UserExistsException("User with this email already exists.");
    }

    std::string hashedPassword = Authentication::hashPassword(password);
    User newUser(0, username, email, hashedPassword, ""); // ID and createdAt will be set by repository
    newUser = userRepository_.save(newUser);
    NEURAX_LOG("User registered successfully. ID: " << newUser.getId());
    return newUser;
}

std::string NeuraxCore::loginUser(const std::string& email, const std::string& password) {
    NEURAX_LOG("Attempting to log in user with email: " << email);

    if (email.empty() || password.empty()) {
        throw InvalidInputException("Email and password cannot be empty.");
    }

    std::optional<User> userOpt = userRepository_.findByEmail(email);
    if (!userOpt.has_value()) {
        throw AuthenticationException("Invalid credentials: User not found.");
    }

    const User& user = userOpt.value();
    if (!Authentication::verifyPassword(password, user.getPasswordHash())) {
        throw AuthenticationException("Invalid credentials: Password mismatch.");
    }

    std::string token = Authentication::generateToken(user.getId(), user.getUsername());
    NEURAX_LOG("User logged in successfully. ID: " << user.getId());
    return token;
}

std::optional<User> NeuraxCore::getUserById(long long userId) {
    NEURAX_LOG("Fetching user by ID: " << userId);
    return userRepository_.findById(userId);
}

// --- Product Management ---
std::vector<Product> NeuraxCore::getAllProducts() {
    NEURAX_LOG("Fetching all products.");
    return productRepository_.findAll();
}

std::optional<Product> NeuraxCore::getProductById(long long productId) {
    NEURAX_LOG("Fetching product by ID: " << productId);
    return productRepository_.findById(productId);
}

Product NeuraxCore::createProduct(long long actingUserId, const std::string& name, const std::string& description,
                                  double price, int stockQuantity) {
    NEURAX_LOG("User " << actingUserId << " attempting to create product: " << name);
    if (!Authorization::hasPermission(actingUserId, "create_product")) {
        throw PermissionDeniedException("User does not have permission to create products.");
    }
    if (name.empty() || price < 0 || stockQuantity < 0) {
        throw InvalidInputException("Product name cannot be empty, price and stock quantity must be non-negative.");
    }

    Product newProduct(0, name, description, price, stockQuantity, "", "");
    newProduct = productRepository_.save(newProduct);
    NEURAX_LOG("Product created successfully. ID: " << newProduct.getId());
    return newProduct;
}

Product NeuraxCore::updateProduct(long long actingUserId, long long productId, const std::string& name,
                                  const std::string& description, double price, int stockQuantity) {
    NEURAX_LOG("User " << actingUserId << " attempting to update product ID: " << productId);
    if (!Authorization::hasPermission(actingUserId, "edit_product")) {
        throw PermissionDeniedException("User does not have permission to edit products.");
    }

    std::optional<Product> existingProductOpt = productRepository_.findById(productId);
    if (!existingProductOpt.has_value()) {
        throw NotFoundException("Product not found.");
    }
    if (name.empty() || price < 0 || stockQuantity < 0) {
        throw InvalidInputException("Product name cannot be empty, price and stock quantity must be non-negative.");
    }

    Product productToUpdate = existingProductOpt.value();
    productToUpdate.setName(name);
    productToUpdate.setDescription(description);
    productToUpdate.setPrice(price);
    productToUpdate.setStockQuantity(stockQuantity);

    productToUpdate = productRepository_.save(productToUpdate);
    NEURAX_LOG("Product updated successfully. ID: " << productToUpdate.getId());
    return productToUpdate;
}

void NeuraxCore::deleteProduct(long long actingUserId, long long productId) {
    NEURAX_LOG("User " << actingUserId << " attempting to delete product ID: " << productId);
    if (!Authorization::hasPermission(actingUserId, "delete_product")) {
        throw PermissionDeniedException("User does not have permission to delete products.");
    }

    if (!productRepository_.remove(productId)) {
        throw NotFoundException("Product not found or could not be deleted.");
    }
    NEURAX_LOG("Product deleted successfully. ID: " << productId);
}

// --- Order Management ---
Order NeuraxCore::placeOrder(long long userId, const std::map<long long, int>& productQuantities) {
    NEURAX_LOG("User " << userId << " attempting to place an order.");
    if (!Authorization::hasPermission(userId, "place_order")) {
        throw PermissionDeniedException("User does not have permission to place orders.");
    }
    if (productQuantities.empty()) {
        throw InvalidInputException("Order must contain at least one product.");
    }

    double totalAmount = 0.0;
    std::vector<std::pair<Product, int>> itemsToOrder; // To store product and quantity for processing

    for (const auto& entry : productQuantities) {
        long long productId = entry.first;
        int quantity = entry.second;

        if (quantity <= 0) {
            throw InvalidInputException("Product quantity must be positive.");
        }

        std::optional<Product> productOpt = productRepository_.findById(productId);
        if (!productOpt.has_value()) {
            throw NotFoundException("Product with ID " + std::to_string(productId) + " not found.");
        }
        Product product = productOpt.value();

        if (product.getStockQuantity() < quantity) {
            throw OutOfStockException("Not enough stock for product: " + product.getName() + ". Available: " + std::to_string(product.getStockQuantity()));
        }

        itemsToOrder.push_back({product, quantity});
        totalAmount += product.getPrice() * quantity;
    }

    // Create the order
    Order newOrder(0, userId, "", totalAmount, Order::Status::PENDING, "", "");
    newOrder = orderRepository_.save(newOrder);

    // Create order items and update product stock
    for (auto& item : itemsToOrder) {
        Product& product = item.first;
        int quantity = item.second;

        OrderItem orderItem(newOrder.getId(), product.getId(), quantity, product.getPrice());
        orderItemRepository_.save(orderItem);

        // Update product stock
        product.setStockQuantity(product.getStockQuantity() - quantity);
        productRepository_.save(product); // Save updated product
    }

    NEURAX_LOG("Order placed successfully. Order ID: " << newOrder.getId() << ", Total: " << std::fixed << std::setprecision(2) << totalAmount);
    return newOrder;
}

std::vector<Order> NeuraxCore::getUserOrders(long long userId) {
    NEURAX_LOG("Fetching orders for user ID: " << userId);
    if (!Authorization::hasPermission(userId, "view_own_orders")) {
         // Though this is implicitly checked by findByUserId, we add explicit check for consistency
         throw PermissionDeniedException("User does not have permission to view orders.");
    }
    return orderRepository_.findByUserId(userId);
}

std::optional<Order> NeuraxCore::getOrderById(long long actingUserId, long long orderId) {
    NEURAX_LOG("User " << actingUserId << " attempting to get order by ID: " << orderId);
    std::optional<Order> orderOpt = orderRepository_.findById(orderId);
    if (!orderOpt.has_value()) {
        return std::nullopt; // Order not found
    }

    const Order& order = orderOpt.value();
    // Check if acting user is owner or has admin permission
    if (!Authorization::isOwner(actingUserId, order.getUserId()) && !Authorization::hasPermission(actingUserId, "view_all_orders")) {
        throw PermissionDeniedException("Access denied to this order.");
    }
    return orderOpt;
}

std::vector<OrderItem> NeuraxCore::getOrderItems(long long orderId) {
    NEURAX_LOG("Fetching order items for order ID: " << orderId);
    // Authorization for viewing order items should be handled by the getOrderById check
    return orderItemRepository_.findByOrderId(orderId);
}
``````cmake
cmake_minimum_required(VERSION 3.10)
project(MyBackendProject LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set build type to Release by default if not specified
if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build, options are: Debug Release MinSizeRel RelWithDebInfo." FORCE)
endif()

# Set output directories
set(EXECUTABLE_OUTPUT_PATH "${CMAKE_BINARY_DIR}/bin")
set(LIBRARY_OUTPUT_PATH "${CMAKE_BINARY_DIR}/lib")

# Include directories
include_directories(
    include
    include/models
    include/auth
    include/api
    include/utils
    include/data    # Add the Data repository header directory
    include/neurax  # Add the NeuraxCore header directory
)

# Source files
set(SOURCE_FILES
    src/main.cpp
    # C++ Model source files
    src/models/User.cpp
    src/models/Product.cpp
    src/models/Order.cpp
    src/models/OrderItem.cpp
    # Authentication and Authorization source files
    src/auth/Authentication.cpp
    src/auth/Authorization.cpp
    # API Framework source files
    src/api/Request.cpp
    src/api/Response.cpp
    # Error Handling source files
    src/utils/ErrorHandler.cpp
    # Data Repository source files
    src/data/UserRepository.cpp
    src/data/ProductRepository.cpp
    src/data/OrderRepository.cpp
    src/data/OrderItemRepository.cpp
    # Neurax Core Logic source files
    src/neurax/NeuraxCore.cpp
)

# Add the main executable
add_executable(my_backend_app ${SOURCE_FILES})

# Link libraries (if any)
# For JSON serialization, if using nlohmann/json, you would add it here if installed via system or CPM.
# Example: find_package(nlohmann_json CONFIG REQUIRED)
# target_link_libraries(my_backend_app PRIVATE nlohmann_json::nlohmann_json)

# Optional: Add compiler flags for warnings and debug macros
if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(my_backend_app PUBLIC
        -Wall
        -Wextra
        -Wpedantic
        -Werror # Treat warnings as errors
        # -Wshadow # Enable this for more strict shadow warnings
    )
    # Add debug flags for auth and neurax modules to see messages
    if (CMAKE_BUILD_TYPE STREQUAL "Debug")
        target_compile_definitions(my_backend_app PUBLIC DEBUG_AUTH DEBUG_NEURAX)
    endif()
endif()

# Install rules (optional for deployment)
install(TARGETS my_backend_app DESTINATION bin)
```