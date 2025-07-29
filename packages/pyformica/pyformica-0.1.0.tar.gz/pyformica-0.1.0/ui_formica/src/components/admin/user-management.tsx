"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import {getToken} from "@/lib/auth";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";

type Role = "operator" | "admin"

interface User {
  id: string
  name: string
  email: string
  role: Role
  isSuperuser: boolean
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // Load users from localStorage on component mount
  useEffect(() => {
    const fetchUsers = async () => {
      const { data } = await client.get(`${API_URL}/users`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setUsers(data)
    }

    fetchUsers()
  }, [])

  // Save users to localStorage whenever they change
  useEffect(() => {
    if (users.length > 0) {
      localStorage.setItem("users", JSON.stringify(users))
    }
  }, [users])

  const handleRoleChange = async (userId: string, newRole: Role) => {
    await client.patch(`${API_URL}/users/${userId}`,
      { role: newRole },
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
    setUsers(users.map((user) => (user.id === userId ? { ...user, role: newRole } : user)))
  }

  // const handleCreateUser = () => {
  //   const newUserId = Math.random().toString(36).substring(2, 9)
  //   const userToAdd = {
  //     id: newUserId,
  //     name: newUser.name,
  //     email: newUser.email,
  //     role: newUser.role,
  //   }
  //
  //   setUsers([...users, userToAdd])
  //
  //   // Reset form
  //   setNewUser({
  //     name: "",
  //     email: "",
  //     password: "",
  //     role: "user",
  //   })
  // }

  const filteredUsers = users.filter(
    (user) =>
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-64">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search users..."
            className="pl-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/*<Dialog>*/}
        {/*  <DialogTrigger asChild>*/}
        {/*    <Button>*/}
        {/*      <PlusCircle className="mr-2 h-4 w-4" />*/}
        {/*      Add User*/}
        {/*    </Button>*/}
        {/*  </DialogTrigger>*/}
        {/*  <DialogContent>*/}
        {/*    <DialogHeader>*/}
        {/*      <DialogTitle>Create New User</DialogTitle>*/}
        {/*    </DialogHeader>*/}
        {/*    <div className="grid gap-4 py-4">*/}
        {/*      <div className="grid grid-cols-4 items-center gap-4">*/}
        {/*        <Label htmlFor="name" className="text-right">*/}
        {/*          Name*/}
        {/*        </Label>*/}
        {/*        <Input*/}
        {/*          id="name"*/}
        {/*          value={newUser.name}*/}
        {/*          onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}*/}
        {/*          className="col-span-3"*/}
        {/*        />*/}
        {/*      </div>*/}
        {/*      <div className="grid grid-cols-4 items-center gap-4">*/}
        {/*        <Label htmlFor="email" className="text-right">*/}
        {/*          Email*/}
        {/*        </Label>*/}
        {/*        <Input*/}
        {/*          id="email"*/}
        {/*          type="email"*/}
        {/*          value={newUser.email}*/}
        {/*          onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}*/}
        {/*          className="col-span-3"*/}
        {/*        />*/}
        {/*      </div>*/}
        {/*      <div className="grid grid-cols-4 items-center gap-4">*/}
        {/*        <Label htmlFor="password" className="text-right">*/}
        {/*          Password*/}
        {/*        </Label>*/}
        {/*        <Input*/}
        {/*          id="password"*/}
        {/*          type="password"*/}
        {/*          value={newUser.password}*/}
        {/*          onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}*/}
        {/*          className="col-span-3"*/}
        {/*        />*/}
        {/*      </div>*/}
        {/*      <div className="grid grid-cols-4 items-center gap-4">*/}
        {/*        <Label htmlFor="role" className="text-right">*/}
        {/*          Role*/}
        {/*        </Label>*/}
        {/*        <Select value={newUser.role} onValueChange={(value) => setNewUser({ ...newUser, role: value as Role })}>*/}
        {/*          <SelectTrigger className="col-span-3">*/}
        {/*            <SelectValue placeholder="Select role" />*/}
        {/*          </SelectTrigger>*/}
        {/*          <SelectContent>*/}
        {/*            <SelectItem value="operator">Operator</SelectItem>*/}
        {/*            <SelectItem value="admin">Admin</SelectItem>*/}
        {/*          </SelectContent>*/}
        {/*        </Select>*/}
        {/*      </div>*/}
        {/*    </div>*/}
        {/*    <DialogFooter>*/}
        {/*      <DialogClose asChild>*/}
        {/*        <Button type="button" variant="outline">*/}
        {/*          Cancel*/}
        {/*        </Button>*/}
        {/*      </DialogClose>*/}
        {/*      <DialogClose asChild>*/}
        {/*        <Button type="button" onClick={handleCreateUser}>*/}
        {/*          Create*/}
        {/*        </Button>*/}
        {/*      </DialogClose>*/}
        {/*    </DialogFooter>*/}
        {/*  </DialogContent>*/}
        {/*</Dialog>*/}
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              {/*<TableHead className="w-[100px]">Disable</TableHead>*/}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredUsers.length > 0 ? (
              filteredUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  {!user.isSuperuser ? (
                    <TableCell>
                      <Select value={user.role} onValueChange={(value) => handleRoleChange(user.id, value as Role)}>
                        <SelectTrigger className="w-[130px]">
                          <SelectValue placeholder="Select role" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="operator" className="text-fuchsia-600">Operator</SelectItem>
                          <SelectItem value="admin" className="text-blue-600">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                  ) : (<TableCell className="text-orange-600">Superuser</TableCell>)}
                  {/*<TableCell>*/}
                  {/*  <Button variant="destructive" size="sm">*/}
                  {/*    Disable*/}
                  {/*  </Button>*/}
                  {/*</TableCell>*/}
                  {/*<TableCell>*/}
                  {/*  <Button variant="ghost" size="sm">*/}
                  {/*    Edit*/}
                  {/*  </Button>*/}
                  {/*</TableCell>*/}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-4">
                  No users found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
