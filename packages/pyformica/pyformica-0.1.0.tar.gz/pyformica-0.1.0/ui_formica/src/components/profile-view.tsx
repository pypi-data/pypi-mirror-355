"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Save, User } from "lucide-react"
import MainLayout from "./main-layout"
import {getToken} from "@/lib/auth.ts";
import applyCaseMiddleware from "axios-case-converter";
import axios from "axios";

interface User {
  id: string,
  name: string,
  role: "admin" | "operator",
  createdAt: string
  email: string
  isSuperuser: boolean
}

export default function ProfileView() {
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())
  const [user, setUser] = useState<User | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    email: "",
  })


  useEffect(() => {
    const fetchUser = async () => {
      const {data} = await client.get(`${API_URL}/users/me`,
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })
      setUser(data)
      setFormData({name: data.name, email: data.email})
    }
    fetchUser()
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })
  }

  const handleProfileUpdate = async (e: React.FormEvent) => {
    if (user === null) {
      console.log("User is null")
      return
    }
    e.preventDefault()
    await client.patch(`${API_URL}/users/${user.id}`,
        { name: formData.name, email: formData.email },
        {
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        })
    
    setUser({
      ...user!,
      name: formData.name,
      email: formData.email,
    })
    alert("Profile updated successfully!")
  }

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">User Profile</h1>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          <Card className="md:w-80">
            <CardHeader>
              <div className="flex justify-center">
                <Avatar className="h-24 w-24">
                  <AvatarImage src={"/placeholder.svg?height=96&width=96"} alt={user?.name} />
                  <AvatarFallback>
                    {user?.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
              </div>
              <CardTitle className="text-center mt-2">{user?.name}</CardTitle>
              <CardDescription className="text-center">{user?.email}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-center">
                <Badge variant="outline" className="flex items-center gap-1">
                  <User className="h-3 w-3" />
                  {user?.isSuperuser ? "Superuser" : (user?.role === "admin" ? "Administrator" : "Operator")}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground text-center">
                Member since {new Date().getFullYear() - 2}
              </div>
            </CardContent>
          </Card>

          <div className="flex-1">
            <Tabs defaultValue="profile" className="w-full">
              <TabsList className="grid w-full grid-cols-1">
                <TabsTrigger value="profile" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Profile
                </TabsTrigger>
              </TabsList>

              <TabsContent value="profile" className="space-y-4 pt-4">
                <Card>
                  <form onSubmit={handleProfileUpdate}>
                    <CardHeader>
                      <CardTitle>Profile Information</CardTitle>
                      <CardDescription>Update your account information</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="name">Full Name</Label>
                        <Input id="name" name="name" value={formData.name} onChange={handleInputChange} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          value={formData.email}
                          onChange={handleInputChange}
                        />
                      </div>
                    </CardContent>
                    <CardFooter>
                      <Button type="submit" className="flex items-center gap-2 mt-2">
                        <Save className="h-4 w-4" />
                        Save Changes
                      </Button>
                    </CardFooter>
                  </form>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
